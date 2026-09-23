"""Unified study-task summary + ETA (single source of truth).

Both the homepage and the study page read ``compute_study_summary``, so they can
never disagree about "how many tasks today" or "how long will it take".

Semantics:
- ``total_tasks`` = today's session size = ``min(daily_goal, review_due + new)``
  (the study queue returns review-due first, then new words, capped at the
  daily goal — it does *not* pad with not-yet-due words).
- ``remaining_tasks`` = ``max(0, total_tasks - completed_today)``.
- ETA = ``remaining_tasks * secs_per_word``, where ``secs_per_word`` is the
  user's historical average (from learning events) or a single default.
"""

import math
from datetime import date

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from core import _get_active_book_id, _get_progress_stats_sql, _get_setting, _set_setting
from models import LearningEvent, DailyStats

DEFAULT_DAILY_GOAL = 20
DEFAULT_SECS_PER_WORD = 30
MIN_SECS_PER_WORD = 15
MAX_SECS_PER_WORD = 120
MIN_HISTORY = 10  # min learning events before we trust the historical average

_DAILY_GOAL_KEY = "daily_goal"


def get_daily_goal(db: Session) -> int:
    raw = _get_setting(db, _DAILY_GOAL_KEY)
    try:
        return max(1, min(100, int(raw)))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_GOAL


def set_daily_goal(db: Session, goal: int) -> int:
    value = max(1, min(100, int(goal)))
    _set_setting(db, _DAILY_GOAL_KEY, str(value))
    db.commit()
    return value


def avg_secs_per_word(db: Session) -> float:
    """Historical average time per word (seconds), or the unified default.

    Uses the average answer time from learning events once the user has enough
    history; otherwise falls back to a single default. The value is clamped so a
    fast answerer doesn't collapse the ETA to a few seconds.
    """
    count = (
        db.query(sa_func.count(LearningEvent.id))
        .filter(LearningEvent.response_time_ms > 0)
        .scalar()
    ) or 0
    if count < MIN_HISTORY:
        return float(DEFAULT_SECS_PER_WORD)

    avg_ms = (
        db.query(sa_func.avg(LearningEvent.response_time_ms))
        .filter(LearningEvent.response_time_ms > 0)
        .scalar()
    )
    secs = float(avg_ms or 0) / 1000.0
    return max(MIN_SECS_PER_WORD, min(MAX_SECS_PER_WORD, secs))


def format_estimated_time(seconds: float) -> str:
    """Unified rounding: <1 min → "约 1 分钟", else round up to minutes."""
    if seconds <= 0:
        return "今天的任务已完成"
    minutes = max(1, math.ceil(seconds / 60))
    return f"约 {minutes} 分钟"


def completed_today(db: Session) -> int:
    today = date.today().isoformat()
    row = db.query(DailyStats).filter(DailyStats.date == today).first()
    return int(row.words_studied or 0) if row else 0


def compute_study_summary(db: Session, bid: int | None = None) -> dict:
    if bid is None:
        bid = _get_active_book_id(db)

    daily_goal = get_daily_goal(db)
    stats = _get_progress_stats_sql(db, bid) if bid else {"total": 0, "new": 0, "review_due": 0, "studied": 0}

    review_due = int(stats.get("review_due", 0) or 0)
    new_available = int(stats.get("new", 0) or 0)

    total_tasks = min(daily_goal, review_due + new_available)
    review_tasks = min(review_due, daily_goal)
    new_tasks = max(0, total_tasks - review_tasks)

    remaining_tasks = max(0, total_tasks - completed_today(db))
    estimated_seconds = round(remaining_tasks * avg_secs_per_word(db))

    return {
        "daily_goal": daily_goal,
        "total_tasks": total_tasks,
        "new_tasks": new_tasks,
        "review_tasks": review_tasks,
        "remaining_tasks": remaining_tasks,
        "estimated_seconds": estimated_seconds,
        "display_text": format_estimated_time(estimated_seconds),
    }
