"""Dashboard and statistics routes."""

from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models import Word, StudyRecord, DailyStats, Book
from schemas import DashboardOut, StatsOut
from core import (
    _get_active_book_id, _book_id_int, _book_id_str, _get_progress_stats_sql,
)

router = APIRouter()


@router.get("/api/dashboard", response_model=DashboardOut)
def get_dashboard(
    book_id: str = Query(None, description="Book ID; uses active book if omitted"),
    db: Session = Depends(get_db),
):
    """Get dashboard data from SQLite."""
    if book_id:
        bid = _book_id_int(db, book_id)
    else:
        bid = _get_active_book_id(db)
        book_id = _book_id_str(db, bid)

    stats = _get_progress_stats_sql(db, bid)
    total = stats["total"]

    active_book_info = None
    if book_id:
        book = db.query(Book).filter(Book.id == bid).first()
        active_book_info = {
            "id": book_id,
            "book_name": book.book_name if book else book_id,
            "word_count": total,
            "studied_count": stats["studied"],
            "mastered_count": stats["mastered"],
            "review_due": stats["review_due"],
        }

    today = date.today()
    today_str = today.isoformat()
    daily = db.query(DailyStats).filter(DailyStats.date == today_str).first()

    # ── Streak calculation ──
    streak = 0
    check_date = date.today()
    while True:
        ds = db.query(DailyStats).filter(DailyStats.date == check_date.isoformat()).first()
        if ds and (ds.words_studied or 0) > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # ── Heatmap: last 30 days ──
    heatmap = []
    for i in range(29, -1, -1):
        d = date.today() - timedelta(days=i)
        ds = db.query(DailyStats).filter(DailyStats.date == d.isoformat()).first()
        heatmap.append({
            "date": d.isoformat(),
            "count": ds.words_studied if ds else 0,
            "minutes": ds.minutes_studied if ds else 0,
        })

    # ── Avg daily words ──
    last_7 = [h for h in heatmap[-7:] if h["count"] > 0]
    avg_daily = round(sum(h["count"] for h in last_7) / max(1, len(last_7)), 1)

    # ── Estimated completion ──
    remaining = total - stats["studied"]
    est_days = round(remaining / avg_daily) if avg_daily > 0 and remaining > 0 else 0

    # ── Recent records ──
    recent = (
        db.query(StudyRecord)
        .order_by(StudyRecord.studied_at.desc())
        .limit(10)
        .all()
    )
    recent_records = [
        {
            "word": (db.query(Word.english).filter(Word.id == r.word_id).scalar() or "?"),
            "result": r.result,
            "studied_at": r.studied_at.isoformat() if r.studied_at else "",
        }
        for r in recent
    ]

    # ── Today's new words (words first studied today) ──
    today_start = datetime(today.year, today.month, today.day)
    today_new = db.query(StudyRecord).filter(
        StudyRecord.studied_at >= today_start,
        StudyRecord.review_stage == 0,
    ).count()

    # ── Total study minutes ──
    total_minutes = db.query(sa_func.sum(DailyStats.minutes_studied)).scalar() or 0

    return {
        "today_words_count": stats["review_due"],
        "streak_days": streak,
        "total_mastered": stats["mastered"],
        "total_words": total,
        "today_studied": daily.words_studied if daily else 0,
        "progress_percent": round((stats["mastered"] / total) * 100, 1) if total > 0 else 0.0,
        "recent_records": recent_records,
        "today_minutes": stats.get("today_minutes", 0),
        "today_new_words": today_new,
        "remaining_words": remaining,
        "avg_daily_words": avg_daily,
        "est_completion_days": est_days,
        "total_minutes": int(total_minutes),
        "heatmap": heatmap,
        "active_book": active_book_info,
    }


@router.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    today_str = date.today().isoformat()
    daily = db.query(DailyStats).filter(DailyStats.date == today_str).first()
    today_studied = (daily.words_studied or 0) if daily else 0
    today_correct = (daily.correct_count or 0) if daily else 0
    today_total = (daily.total_reviews or 0) if daily else 0

    total_records = db.query(StudyRecord).count()
    total_mastered = db.query(Word).filter(Word.is_mastered == True).count()
    total_words = db.query(Word).count()
    favorite_count = db.query(Word).filter(Word.is_favorite == True).count()

    # Overall accuracy
    total_correct = db.query(Word).with_entities(sa_func.sum(Word.correct_count)).scalar() or 0
    total_reviews_all = db.query(Word).with_entities(sa_func.sum(Word.review_count)).scalar() or 0
    overall_acc = round(total_correct / total_reviews_all, 2) if total_reviews_all > 0 else 0.0

    # Streak
    streak = 0
    check_date = date.today()
    while True:
        ds = db.query(DailyStats).filter(DailyStats.date == check_date.isoformat()).first()
        if ds and (ds.words_studied or 0) > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Proficiency distribution
    dist = {}
    for level in range(6):
        count = db.query(Word).filter(Word.proficiency == level).count()
        dist[str(level)] = count

    return {
        "today_studied": today_studied,
        "total_studied": total_records,
        "total_mastered": total_mastered,
        "streak_days": streak,
        "total_words": total_words,
        "favorite_count": favorite_count,
        "today_correct": today_correct,
        "today_total": today_total,
        "overall_accuracy": overall_acc,
        "proficiency_distribution": dist,
    }


@router.get("/api/stats/weekly")
def get_weekly_stats(db: Session = Depends(get_db)):
    """Get stats for the last 7 days for trend charts."""
    result = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        ds = db.query(DailyStats).filter(DailyStats.date == d.isoformat()).first()
        result.append({
            "date": d.isoformat(),
            "words_studied": ds.words_studied if ds else 0,
            "words_mastered": ds.words_mastered if ds else 0,
            "correct_count": ds.correct_count if ds else 0,
            "total_reviews": ds.total_reviews if ds else 0,
            "accuracy": round(ds.correct_count / ds.total_reviews, 2) if (ds and ds.total_reviews) else 0,
        })
    return result


@router.get("/api/stats/errors")
def get_error_words(db: Session = Depends(get_db)):
    """Get words with low accuracy for error analysis."""
    words = (
        db.query(Word)
        .filter(Word.review_count >= 2)
        .filter(Word.accuracy_rate < 1.0)
        .order_by(Word.accuracy_rate.asc())
        .limit(30)
        .all()
    )

    return {
        "error_words": [
            {
                "id": w.id,
                "english": w.english,
                "chinese": w.chinese,
                "wrong_count": w.review_count - int(w.correct_count),
                "accuracy_rate": round(w.accuracy_rate, 2),
                "proficiency": w.proficiency,
            }
            for w in words
            if (w.review_count - int(w.correct_count)) > 0
        ],
        "total": len(words),
    }


@router.get("/api/debug/word-states")
def debug_word_states(
    book_id: str = Query(None, description="Book ID; uses active book if omitted"),
    db: Session = Depends(get_db),
):
    """Debug endpoint: show word state distribution from SQLite."""
    if book_id:
        bid = _book_id_int(db, book_id)
    else:
        bid = _get_active_book_id(db)
        book_id = _book_id_str(db, bid)

    stats = _get_progress_stats_sql(db, bid) if bid else {"total": 0, "new": 0, "learning": 0, "mastered": 0, "studied": 0, "review_due": 0}

    return {
        "book": {"id": book_id, "name": book_id, "is_active": True},
        "counts": {
            "total": stats["total"],
            "new": stats["new"],
            "learning": stats["learning"],
            "mastered": stats["mastered"],
            "review_due": stats["review_due"],
            "stale_new": 0,
        },
        "review_due_samples": [],
        "algorithm": {
            "rule": "只有 status=learning 且 next_review <= now 的单词才计入待复习",
            "new_words_handling": "status=new 的单词不计入待复习，按需加入学习队列",
            "reset_behavior": "重置后删除所有进度，全部单词恢复 new",
        },
    }
