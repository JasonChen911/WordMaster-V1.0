"""Learning Event System — one place to record raw learning behaviors.

Every study review, exercise answer, reading lookup and confusion test writes a
structured ``LearningEvent`` row. These rows are *facts*; AI insight is a
separate interpretation layer and is never mixed in here.
"""

import json
import logging
from datetime import datetime, date

from sqlalchemy.orm import Session

from models import LearningEvent

logger = logging.getLogger(__name__)


def _json_safe(value):
    """Convert a nested dict to a JSON-serializable form (datetimes → iso)."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value

# Result mapping for review ratings → correct/incorrect.
RATING_TO_RESULT = {
    "again": "incorrect",
    "hard": "incorrect",
    "good": "correct",
    "easy": "correct",
}

# FSRS result strings used by the study router → canonical rating.
RESULT_TO_RATING = {
    "unknown": "again",
    "fuzzy": "hard",
    "know": "good",
    "too_easy": "easy",
}


def log_event(
    db: Session,
    *,
    word_id: int,
    activity_type: str,
    book_id: int = 0,
    session_id: str = "",
    result: str = "",
    rating: str = "",
    response_time_ms: int = 0,
    user_answer: str = "",
    correct_answer: str = "",
    error_type: str = "",
    source_type: str = "",
    source_id: int = 0,
    fsrs_before: dict | None = None,
    fsrs_after: dict | None = None,
    client_version: str = "",
    algorithm_version: str = "",
) -> LearningEvent | None:
    """Persist one learning event. Never raises — logging must not break study."""
    try:
        event = LearningEvent(
            word_id=word_id,
            book_id=book_id,
            session_id=session_id or "",
            timestamp=datetime.now(),
            activity_type=activity_type,
            result=result,
            rating=rating,
            response_time_ms=int(response_time_ms or 0),
            user_answer=user_answer or "",
            correct_answer=correct_answer or "",
            error_type=error_type or "",
            source_type=source_type or "",
            source_id=int(source_id or 0),
            fsrs_before=json.dumps(_json_safe(fsrs_before), ensure_ascii=False) if fsrs_before else "",
            fsrs_after=json.dumps(_json_safe(fsrs_after), ensure_ascii=False) if fsrs_after else "",
            client_version=client_version or "",
            algorithm_version=algorithm_version or "",
        )
        db.add(event)
        return event
    except Exception as e:  # noqa: BLE001 — event logging is best-effort
        logger.warning("Learning event logging failed: %s", e)
        return None


def error_type_for(result: str, user_answer: str = "", correct_answer: str = "") -> str:
    """Infer a coarse error category from a review/answer result."""
    if result in ("know", "too_easy", "good", "easy", "correct"):
        return "none"
    return "meaning"  # default; caller may override with a more specific type
