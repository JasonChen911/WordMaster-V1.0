"""Mistake book — aggregated, de-duplicated records of wrong answers.

A mistake is recorded once per (word, source). Repeated mistakes increment
``count`` instead of piling up duplicate rows. The ``source`` field keeps daily
review mistakes separate from spelling-game mistakes.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from sqlalchemy.dialects.sqlite import insert

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
        now = datetime.now()
        statement = insert(MistakeRecord).values(
            word_id=word_id, source=source, mistake_type=mistake_type or "",
            count=1, first_occurred_at=now, last_occurred_at=now,
            last_session_id=session_id or "",
        )
        # A game token identifies one settled question, not the whole game.
        # Daily sessions may contain multiple genuine mistakes on the same word.
        same_round = (MistakeRecord.last_session_id != session_id) if source == SOURCE_GAME and session_id else None
        statement = statement.on_conflict_do_update(
            index_elements=["word_id", "source"],
            set_={"count": func.coalesce(MistakeRecord.count, 0) + 1,
                  "last_occurred_at": now,
                  "last_session_id": session_id or "",
                  "mistake_type": case((MistakeRecord.mistake_type == "", mistake_type or ""), else_=MistakeRecord.mistake_type)},
            where=same_round,
        )
        # Keep optional mistake logging from rolling back the study transaction.
        with db.begin_nested():
            db.execute(statement)
        return db.query(MistakeRecord).filter_by(word_id=word_id, source=source).populate_existing().one()
    except Exception as e:
        logger.warning("Mistake record failed: %s", e)
        return None
