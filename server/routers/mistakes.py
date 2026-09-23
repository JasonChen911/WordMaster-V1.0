"""Mistake book routes — list, filter by source, stats, record, remove."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models import Word, MistakeRecord
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
        "source": row.source,
        "source_label": _SOURCE_LABELS.get(row.source, row.source),
        "mistake_type": row.mistake_type or "",
        "count": row.count or 0,
        "first_occurred_at": row.first_occurred_at.isoformat() if row.first_occurred_at else "",
        "last_occurred_at": row.last_occurred_at.isoformat() if row.last_occurred_at else "",
    }


@router.get("/api/mistakes")
def list_mistakes(
    source: str = "all",
    db: Session = Depends(get_db),
):
    """List mistake-book entries, optionally filtered by source.

    ``source`` is one of ``all`` | ``daily`` | ``game``. A word with mistakes in
    both sources appears in both filtered lists and (once) in ``all``.
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


@router.post("/api/mistakes")
async def record_mistake_route(request: Request, db: Session = Depends(get_db)):
    """Record one mistake (upsert by word + source)."""
    try:
        body = await request.json()
    except Exception:
        return {"error": "请求体不是合法 JSON。"}

    word_text = str(body.get("word") or "").strip().lower()
    source = str(body.get("source") or "").strip()
    mistake_type = str(body.get("mistake_type") or "").strip()

    if not word_text:
        return {"error": "缺少单词。"}
    if source not in (SOURCE_DAILY, SOURCE_GAME):
        return {"error": "无效的来源。"}

    word = db.query(Word).filter(Word.english == word_text).first()
    if not word:
        return {"error": "单词不存在。"}

    record_mistake(
        db,
        word_id=word.id,
        source=source,
        mistake_type=mistake_type,
        session_id=str(body.get("session_id") or ""),
    )
    db.commit()
    return {"success": True, "word": word.english, "source": source}


@router.post("/api/mistakes/{word_id}/review")
def add_to_review(word_id: int, db: Session = Depends(get_db)):
    """Put a mistake word back into today's review queue (due now)."""
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return {"error": "单词不存在。"}
    word.next_review = datetime.now()
    if word.study_status == "new":
        word.study_status = "learning"
    db.commit()
    return {"success": True, "word": word.english}


@router.delete("/api/mistakes/{word_id}")
def remove_mistake(word_id: int, db: Session = Depends(get_db)):
    """Remove all mistake records for a word (does NOT touch study data)."""
    deleted = db.query(MistakeRecord).filter(MistakeRecord.word_id == word_id).delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted}
