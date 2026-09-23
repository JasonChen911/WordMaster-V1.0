"""Word study routes: study queue, study recording, reset, favorites."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Word, StudyRecord, DailyStats, WordMemoryState
from schemas import StudyRequest, WordOut
from core import (
    _get_active_book_id, _book_id_int, _book_id_str, _get_book_scoped_word_ids,
    _generate_study_queue_sql,
)
from srs import (
    review_card as fsrs_review,
    is_mastered as fsrs_is_mastered,
    proficiency_from_state,
    explain_state,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/words/today")
def get_today_words(
    book_id: str = Query(None, description="Book ID; uses active book if omitted"),
    db: Session = Depends(get_db),
):
    """Get words due for review from SQLite."""
    if book_id:
        bid = _book_id_int(db, book_id)
    else:
        bid = _get_active_book_id(db)
    if not bid:
        return []
    return _generate_study_queue_sql(db, bid, 20)


@router.get("/api/words/study-queue")
def get_study_queue(
    book_id: str = Query(None, description="Book ID; uses active book if omitted"),
    count: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get a study queue from SQLite with Ebbinghaus priority.

    Priority:
      1. Review-due words (learning, next_review <= now)
      2. New words (never studied)
    """
    if book_id:
        bid = _book_id_int(db, book_id)
    else:
        bid = _get_active_book_id(db)
    if not bid:
        return []
    return _generate_study_queue_sql(db, bid, count)


@router.get("/api/words/all", response_model=list[WordOut])
def get_all_words(db: Session = Depends(get_db)):
    return db.query(Word).order_by(Word.english.asc()).all()


@router.get("/api/words/{word_id}", response_model=WordOut)
def get_word(word_id: int, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return word


@router.get("/api/words/{word_id}/fsrs")
def get_word_fsrs(word_id: int, db: Session = Depends(get_db)):
    """Explainable FSRS memory state for a word — answers "why review today?".

    Returns estimated retention, stability, difficulty, forgetting risk and the
    next review time, or a minimal payload when the word has no review history.
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    mem = db.query(WordMemoryState).filter(WordMemoryState.word_id == word.id).first()
    state = None
    if mem:
        state = {
            "state": mem.state,
            "step": mem.step,
            "stability": mem.stability,
            "difficulty": mem.difficulty,
            "due": mem.due,
            "last_review": mem.last_review,
            "reps": mem.reps,
            "lapses": mem.lapses,
        }

    explanation = explain_state(word.id, state)
    return {
        "word_id": word.id,
        "english": word.english,
        "review_count": word.review_count or 0,
        "has_history": state is not None,
        **explanation,
    }


@router.post("/api/study")
def record_study(req: StudyRequest, db: Session = Depends(get_db)):
    """Record a study result in SQLite."""
    bid = _get_active_book_id(db)

    # Look up word by english text (frontend sends word_id as english string)
    word = db.query(Word).filter(Word.english == str(req.word_id).lower().strip()).first()
    if not word:
        logger.warning(f"Study: word '{req.word_id}' not found in DB")
        return {"message": "Word not found", "word": {"id": req.word_id, "english": req.word_id}}

    now = datetime.now()

    # ── FSRS adaptive review: single source of truth for next_review ──
    mem = db.query(WordMemoryState).filter(WordMemoryState.word_id == word.id).first()
    current_state = None
    if mem:
        current_state = {
            "state": mem.state,
            "step": mem.step,
            "stability": mem.stability,
            "difficulty": mem.difficulty,
            "due": mem.due,
            "last_review": mem.last_review,
            "reps": mem.reps,
            "lapses": mem.lapses,
        }

    fsrs_state = fsrs_review(word.id, current_state, req.result, now=now)

    if not mem:
        mem = WordMemoryState(word_id=word.id)
        db.add(mem)
    mem.state = fsrs_state["state"]
    mem.step = fsrs_state["step"]
    mem.stability = fsrs_state["stability"]
    mem.difficulty = fsrs_state["difficulty"]
    mem.due = fsrs_state["due"]
    mem.last_review = fsrs_state["last_review"]
    mem.reps = fsrs_state["reps"]
    mem.lapses = fsrs_state["lapses"]

    # ── Update legacy fields (kept for stats / dashboard compatibility) ──
    word.review_count = (word.review_count or 0) + 1
    word.last_reviewed_at = now
    word.next_review = fsrs_state["due"]

    if req.result in ("too_easy", "know"):
        word.correct_count = (word.correct_count or 0.0) + 1.0
    elif req.result == "fuzzy":
        word.correct_count = (word.correct_count or 0.0) + 0.5

    word.compute_accuracy()

    mastered = fsrs_is_mastered(fsrs_state)
    if mastered:
        word.study_status = "mastered"
        word.is_mastered = True
    else:
        word.study_status = "learning"
    word.proficiency = proficiency_from_state(fsrs_state, mastered=mastered)

    # ── Record study event ──
    record = StudyRecord(
        word_id=word.id,
        book_id=bid,
        result=req.result,
        review_stage=word.review_stage,
    )
    db.add(record)

    # ── Update daily stats ──
    today_str = now.date().isoformat()
    daily = db.query(DailyStats).filter(DailyStats.date == today_str).first()
    if not daily:
        daily = DailyStats(date=today_str, words_studied=0, total_reviews=0,
                           correct_count=0, words_mastered=0, minutes_studied=0)
        db.add(daily)
        db.flush()
    daily.words_studied = (daily.words_studied or 0) + 1
    daily.total_reviews = (daily.total_reviews or 0) + 1
    if req.result in ("too_easy", "know"):
        daily.correct_count = (daily.correct_count or 0) + 1
    if word.is_mastered:
        daily.words_mastered = (daily.words_mastered or 0) + 1
    daily.minutes_studied = (daily.minutes_studied or 0) + max(1, req.seconds_spent // 60 or 1)

    db.commit()

    logger.info(
        f"Study: word='{word.english}' result={req.result} "
        f"review_count={word.review_count} next_review={word.next_review}"
    )

    explanation = explain_state(word.id, fsrs_state, now=now)
    return {
        "message": "Study recorded",
        "word": {
            "id": word.id,
            "english": word.english,
            "difficulty": word.difficulty or 2.5,
            "is_mastered": bool(word.is_mastered),
            "next_review": word.next_review.isoformat() if word.next_review else "",
            "review_stage": word.review_stage or 0,
            "accuracy_rate": word.accuracy_rate or 0.0,
            "proficiency": word.proficiency or 0,
        },
        "fsrs": explanation,
    }


@router.post("/api/study/reset")
def reset_study_progress(
    book_id: str = Query(None, description="Book ID; uses active book if omitted"),
    db: Session = Depends(get_db),
):
    """Reset all learning progress for a book in SQLite."""
    if book_id:
        bid = _book_id_int(db, book_id)
    else:
        bid = _get_active_book_id(db)
        book_id = _book_id_str(db, bid)

    word_ids = _get_book_scoped_word_ids(db, bid)
    if word_ids:
        db.query(Word).filter(Word.id.in_(word_ids)).update({
            Word.study_status: "new",
            Word.review_count: 0,
            Word.correct_count: 0.0,
            Word.review_stage: 0,
            Word.proficiency: 0,
            Word.is_mastered: False,
            Word.accuracy_rate: 0.0,
            Word.next_review: datetime.now(),
            Word.last_reviewed_at: None,
        }, synchronize_session=False)
        db.query(StudyRecord).filter(StudyRecord.book_id == bid).delete(synchronize_session=False)
        db.query(WordMemoryState).filter(WordMemoryState.word_id.in_(word_ids)).delete(synchronize_session=False)
        db.commit()

    logger.info(f"Reset study progress for book '{book_id}' (id={bid})")
    return {"success": True, "message": "Study progress has been reset.", "book_id": book_id}


@router.post("/api/words/{word_id}/favorite")
def toggle_favorite(word_id: int, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return {"error": "Word not found"}
    word.is_favorite = not word.is_favorite
    db.commit()
    return {"is_favorite": word.is_favorite}
