"""Mistake book — aggregated, de-duplicated records of wrong answers.

A mistake is recorded once per (word, source). Repeated mistakes increment
``count`` instead of piling up duplicate rows. The ``source`` field keeps daily
review mistakes separate from spelling-game mistakes.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from models import MistakeRecord

logger = logging.getLogger(__name__)

# Canonical mistake sources.
SOURCE_DAILY = "daily"
SOURCE_GAME = "game"

# Coarse mistake-type labels.
TYPE_MEANING = "meaning"
TYPE_SPELLING = "spelling"


def record_mistake(
    db: Session,
    *,
    word_id: int,
    source: str,
    mistake_type: str = "",
    session_id: str = "",
) -> MistakeRecord | None:
    """Upsert a mistake record for (word, source). Never raises."""
    if not word_id or not source:
        return None
    try:
        row = (
            db.query(MistakeRecord)
            .filter(MistakeRecord.word_id == word_id, MistakeRecord.source == source)
            .first()
        )
        if row:
            row.count = (row.count or 0) + 1
            row.last_occurred_at = datetime.now()
            if session_id:
                row.last_session_id = session_id
            if mistake_type and not row.mistake_type:
                row.mistake_type = mistake_type
        else:
            row = MistakeRecord(
                word_id=word_id,
                source=source,
                mistake_type=mistake_type or "",
                count=1,
                last_session_id=session_id or "",
            )
            db.add(row)
        return row
    except Exception as e:  # noqa: BLE001 — mistake logging is best-effort
        logger.warning("Mistake record failed: %s", e)
        return None
