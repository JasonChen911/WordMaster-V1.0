"""Mistake book routes — list, filter by source, stats, record, remove."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models import Word, MistakeRecord, WordMemoryState, BookWord
from core import _get_active_book_id, _book_id_str
from mistakes import record_mistake, SOURCE_DAILY, SOURCE_GAME

logger = logging.getLogger(__name__)

router = APIRouter()

_SOURCE_LABELS = {SOURCE_DAILY: "日常错误", SOURCE_GAME: "游戏错误"}


def _serialize(row: MistakeRecord, word: Word) -> dict:
    return {
        "id": row.id,
        "word_id": word.id,
        "english": word.english,
        "chinese": word.chinese or "",
        "phonetic": word.phonetic or "",
        "example_en": word.example_en or "",
        "example_cn": word.example_cn or "",
        "study_status": word.study_status or "new",
        "source": row.source,
        "source_label": _SOURCE_LABELS.get(row.source, row.source),
        "mistake_type": row.mistake_type or "",
        "count": row.count or 0,
        "first_occurred_at": row.first_occurred_at.isoformat() if row.first_occurred_at else "",
        "last_occurred_at": row.last_occurred_at.isoformat() if row.last_occurred_at else "",
    }


@router.get("/api/mistakes")
def list_mistakes(
    source: Literal["all", "daily", "game"] = "all",
    db: Session = Depends(get_db),
):
    """List mistake-book entries, optionally filtered by source.

    ``source`` is one of ``all`` | ``daily`` | ``game``. A word with mistakes in
    both sources appears in both filtered lists. The UI groups all rows by word_id.
    """
    query = db.query(MistakeRecord, Word).join(Word, Word.id == MistakeRecord.word_id)
    if source in (SOURCE_DAILY, SOURCE_GAME):
        query = query.filter(MistakeRecord.source == source)

    rows = query.order_by(MistakeRecord.last_occurred_at.desc()).all()
    return {"mistakes": [_serialize(r, w) for r, w in rows]}


@router.get("/api/mistakes/stats")
def mistake_stats(db: Session = Depends(get_db)):
    """Real counts: total distinct words, daily, game."""
    def count_words(src=None):
        q = db.query(sa_func.count(sa_func.distinct(MistakeRecord.word_id)))
        if src:
            q = q.filter(MistakeRecord.source == src)
        return q.scalar() or 0

    return {
        "total": count_words(),
        "daily": count_words(SOURCE_DAILY),
        "game": count_words(SOURCE_GAME),
    }


class MistakeInput(BaseModel):
    word_id: int | None = Field(default=None, gt=0)
    word: str = ""
    source: Literal["daily", "game"]
    mistake_type: str = Field(default="", max_length=80)
    session_id: str = Field(default="", max_length=160)


@router.post("/api/mistakes")
def record_mistake_route(body: MistakeInput, db: Session = Depends(get_db)):
    """Use the original word ID; retain text compatibility for older clients."""
    if body.word_id is not None:
        word = db.get(Word, body.word_id)
    elif body.word.strip():
        word = db.query(Word).filter(sa_func.lower(Word.english) == body.word.strip().lower()).first()
    else:
        raise HTTPException(422, "缺少单词。")
    if not word:
        raise HTTPException(404, "单词不存在。")
    row = record_mistake(db, word_id=word.id, source=body.source,
                         mistake_type=body.mistake_type, session_id=body.session_id)
    if row is None:
        raise HTTPException(500, "错词保存失败，请重试。")
    db.commit()
    return {"success": True, "word": word.english, "word_id": word.id, "source": body.source}


@router.post("/api/mistakes/{word_id}/review")
def add_to_review(word_id: int, db: Session = Depends(get_db)):
    """Put a mistake word back into today's review queue (due now)."""
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(404, "单词不存在。")
    word.next_review = datetime.now()
    word.study_status = "learning"
    word.is_mastered = False
    memory = db.query(WordMemoryState).filter_by(word_id=word_id).first()
    if memory:
        memory.due = word.next_review
    # Choose the current book if it contains the word, otherwise its original book.
    links = db.query(BookWord).filter_by(word_id=word_id).all()
    active = _get_active_book_id(db)
    bid = next((link.book_id for link in links if link.book_id == active), links[0].book_id if links else None)
    db.commit()
    return {"success": True, "word": word.english, "book_id": _book_id_str(db, bid) if bid else None}


@router.delete("/api/mistakes/{word_id}")
def remove_mistake(word_id: int, db: Session = Depends(get_db)):
    """Remove all mistake records for a word (does NOT touch study data)."""
    deleted = db.query(MistakeRecord).filter(MistakeRecord.word_id == word_id).delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted}
