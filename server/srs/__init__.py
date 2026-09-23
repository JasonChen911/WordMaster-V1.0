"""FSRS adaptive spaced-repetition engine for WordMaster.

Wraps the MIT-licensed ``fsrs`` package (Open Spaced Repetition, 2022) with a
small, WordMaster-facing API. The review scheduler is the single source of
truth for ``next_review``; WordMaster's older Ebbinghaus fields remain only as
backward-compatible display/stats columns.
"""

from .engine import (
    rating_from_result,
    review_card,
    new_card,
    card_from_state,
    retrievability_at,
    explain_state,
    proficiency_from_state,
    RESULT_TO_RATING,
    RATING_TO_RESULT,
    is_mastered,
)

__all__ = [
    "rating_from_result",
    "review_card",
    "new_card",
    "card_from_state",
    "retrievability_at",
    "explain_state",
    "proficiency_from_state",
    "RESULT_TO_RATING",
    "RATING_TO_RESULT",
    "is_mastered",
]
