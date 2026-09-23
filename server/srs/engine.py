"""WordMaster-facing wrapper around the FSRS scheduler.

Copyright notice (MIT, required by the ``fsrs`` dependency):
  fsrs — https://github.com/open-spaced-repetition/py-fsrs
  Copyright (c) 2022 Open Spaced Repetition
  Licensed under the MIT License.

This module adapts the library to WordMaster's data model:
- Maps WordMaster's four answer grades to FSRS ratings.
- Persists FSRS state as plain fields so ``WordMemoryState`` can stay a dumb row.
- Works in naive-local datetime on the outside (matching the rest of the app),
  converting to/from UTC-aware datetimes only at the library boundary.
"""

from datetime import datetime, timedelta, timezone

from fsrs import Card, Rating, Scheduler, State

# WordMaster answer grade → FSRS rating. A single shared scheduler instance is
# cheap (pure math, stateless across cards) and keeps parameters consistent.
RESULT_TO_RATING = {
    "unknown": Rating.Again,    # 不会  → 忘记
    "fuzzy": Rating.Hard,       # 模糊  → 困难
    "know": Rating.Good,        # 认识  → 一般
    "too_easy": Rating.Easy,    # 已掌握 → 简单
}
RATING_TO_RESULT = {v: k for k, v in RESULT_TO_RATING.items()}

# A card is considered "mastered" once it graduates to the Review state and its
# stability exceeds three weeks — a meaningful, explainable mastery threshold.
MASTERED_STABILITY_DAYS = 21.0

# enable_fuzzing=False keeps intervals deterministic, so the "预计 X 天后复习"
# estimate is exact and the schedule is reproducible in tests and demos.
_scheduler = Scheduler(enable_fuzzing=False)


def _local_tz():
    return datetime.now().astimezone().tzinfo


def _to_utc(dt: datetime) -> datetime:
    """Naive-local → timezone-aware UTC (the library requires UTC)."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=_local_tz()).astimezone(timezone.utc)


def _to_local(dt: datetime) -> datetime:
    """Timezone-aware (UTC) → naive-local, matching ``datetime.now()``."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(_local_tz()).replace(tzinfo=None)


def rating_from_result(result: str) -> Rating:
    """Translate a WordMaster answer grade to an FSRS rating (defaults Good)."""
    return RESULT_TO_RATING.get(result, Rating.Good)


def new_card(word_id: int) -> Card:
    """A brand-new learning card for a never-reviewed word."""
    return Card(card_id=int(word_id))


def card_from_state(word_id: int, state: dict | None) -> Card:
    """Rebuild a Card from a ``WordMemoryState``-shaped dict (or a new card)."""
    if not state or state.get("stability") is None:
        return new_card(word_id)

    st = state.get("state")
    try:
        fsrs_state = State(int(st)) if st is not None else State.Learning
    except (TypeError, ValueError):
        fsrs_state = State.Learning

    due = state.get("due")
    last = state.get("last_review")
    return Card(
        card_id=int(word_id),
        state=fsrs_state,
        step=int(state.get("step") or 0),
        stability=float(state.get("stability")),
        difficulty=float(state.get("difficulty")),
        due=_to_utc(due) if due else None,
        last_review=_to_utc(last) if last else None,
    )


def review_card(word_id: int, current_state: dict | None, result: str, now: datetime | None = None) -> dict:
    """Apply one review and return the new FSRS state as a persistable dict.

    Args:
        word_id: the word's integer id (used as the card id).
        current_state: the persisted ``WordMemoryState`` fields, or None if new.
        result: one of "unknown" | "fuzzy" | "know" | "too_easy".
        now: naive-local review time (defaults to ``datetime.now()``).

    Returns a dict of the fields to write back (all naive-local datetimes).
    """
    review_at = now or datetime.now()
    rating = rating_from_result(result)

    card = card_from_state(word_id, current_state)
    new_card, _log = _scheduler.review_card(card, rating, review_datetime=_to_utc(review_at))

    is_lapse = rating == Rating.Again
    return {
        "state": int(new_card.state.value),
        "step": new_card.step,
        "stability": new_card.stability,
        "difficulty": new_card.difficulty,
        "due": _to_local(new_card.due),
        "last_review": _to_local(new_card.last_review),
        "reps": (int(current_state.get("reps") or 0) + 1) if current_state else 1,
        "lapses": (int(current_state.get("lapses") or 0) + (1 if is_lapse else 0)) if current_state else (1 if is_lapse else 0),
    }


def retrievability_at(word_id: int, state: dict | None, at: datetime | None = None) -> float:
    """Current retrieval probability (0..1) for a word, given its FSRS state."""
    if not state or state.get("stability") is None:
        return 0.0
    card = card_from_state(word_id, state)
    when = at or datetime.now()
    try:
        return float(_scheduler.get_card_retrievability(card, current_datetime=_to_utc(when)))
    except Exception:
        return 0.0


def is_mastered(state: dict | None) -> bool:
    """True once the card graduated to Review and holds a long stability."""
    if not state or state.get("stability") is None:
        return False
    try:
        return int(state.get("state")) == State.Review.value and float(state["stability"]) >= MASTERED_STABILITY_DAYS
    except (TypeError, ValueError):
        return False


def proficiency_from_state(state: dict | None, mastered: bool | None = None) -> int:
    """Map FSRS state to the legacy 0-5 proficiency scale used by the dashboard."""
    if state is None or state.get("stability") is None:
        return 0
    if mastered is None:
        mastered = is_mastered(state)
    if mastered:
        return 5
    try:
        fsrs_state = int(state.get("state"))
        stability = float(state.get("stability") or 0)
    except (TypeError, ValueError):
        return 0
    if fsrs_state == State.Relearning.value:
        return 2
    if fsrs_state == State.Review.value:
        if stability >= 7:
            return 4
        if stability >= 3:
            return 3
        return 2
    # Learning
    return 1 if int(state.get("reps") or 0) > 0 else 0


def explain_state(word_id: int, state: dict | None, now: datetime | None = None) -> dict:
    """Human-readable, explainable view of a word's memory state.

    Returns the numbers behind the "why am I reviewing this today?" question.
    """
    when = now or datetime.now()
    r = retrievability_at(word_id, state, at=when)
    due = state.get("due") if state else None
    stability = (state.get("stability") if state else None) or 0.0

    risk = "high" if r < 0.6 else ("medium" if r < 0.8 else "low")

    return {
        "retrievability": round(r, 4),
        "stability_days": round(float(stability), 2),
        "difficulty": round(float(state.get("difficulty") or 0), 2) if state else None,
        "state": int(state.get("state")) if state and state.get("state") is not None else None,
        "lapses": int(state.get("lapses") or 0) if state else 0,
        "reps": int(state.get("reps") or 0) if state else 0,
        "next_review": due.isoformat() if due else None,
        "forgetting_risk": risk,
    }
