"""Learning Insights routes — real, DB-computed statistics + confusion sets.

Statistics here are always computed from real data. AI (``/api/ai/insights``)
only *interprets* those numbers; it never fabricates them.
"""

import logging
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Word, StudyRecord, DailyStats, WordMemoryState, ConfusionSet,
)
from srs import retrievability_at, explain_state

logger = logging.getLogger(__name__)

router = APIRouter()


def _last_7_days(db: Session) -> dict:
    """Aggregate the last 7 days from daily_stats and study_records."""
    start = date.today() - timedelta(days=6)
    rows = (
        db.query(DailyStats)
        .filter(DailyStats.date >= start.isoformat())
        .all()
    )
    words_studied = sum(r.words_studied or 0 for r in rows)
    reviews = sum(r.total_reviews or 0 for r in rows)
    correct = sum(r.correct_count or 0 for r in rows)
    minutes = sum(r.minutes_studied or 0 for r in rows)
    days_active = sum(1 for r in rows if (r.words_studied or 0) > 0)

    avg_accuracy = round(correct / reviews, 3) if reviews > 0 else 0.0

    # Forgetting rate = "unknown" (forgot) answers / total reviews, last 7 days.
    since = datetime.combine(start, datetime.min.time())
    forgot = (
        db.query(sa_func.count(StudyRecord.id))
        .filter(StudyRecord.studied_at >= since, StudyRecord.result == "unknown")
        .scalar()
    ) or 0
    forgetting_rate = round(forgot / reviews, 3) if reviews > 0 else 0.0

    return {
        "words_studied": words_studied,
        "reviews": reviews,
        "avg_accuracy": avg_accuracy,
        "forgetting_rate": forgetting_rate,
        "minutes": minutes,
        "days_active": days_active,
    }


def _high_risk_words(db: Session, limit: int = 20) -> list[dict]:
    """Words the FSRS model flags as high forgetting risk (lapsed / relearning)."""
    rows = (
        db.query(Word, WordMemoryState)
        .join(WordMemoryState, WordMemoryState.word_id == Word.id)
        .filter(
            Word.study_status != "mastered",
            (WordMemoryState.state == 3) | (WordMemoryState.lapses >= 2),
        )
        .order_by(WordMemoryState.lapses.desc(), WordMemoryState.due.asc())
        .limit(limit)
        .all()
    )
    result = []
    for word, mem in rows:
        state = {
            "state": mem.state, "step": mem.step, "stability": mem.stability,
            "difficulty": mem.difficulty, "due": mem.due, "last_review": mem.last_review,
            "reps": mem.reps, "lapses": mem.lapses,
        }
        r = retrievability_at(word.id, state)
        result.append({
            "id": word.id,
            "english": word.english,
            "chinese": word.chinese or "",
            "retrievability": round(r, 3),
            "lapses": mem.lapses or 0,
            "next_review": mem.due.isoformat() if mem.due else None,
        })
    return result


def _weak_words(db: Session, limit: int = 15) -> list[dict]:
    """Words with the lowest accuracy among studied words."""
    words = (
        db.query(Word)
        .filter(Word.review_count >= 2, Word.accuracy_rate < 1.0)
        .order_by(Word.accuracy_rate.asc(), Word.review_count.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": w.id,
            "english": w.english,
            "chinese": w.chinese or "",
            "wrong_count": (w.review_count or 0) - int(w.correct_count or 0),
            "accuracy_rate": round(w.accuracy_rate or 0, 2),
            "review_count": w.review_count or 0,
        }
        for w in words
        if (w.review_count - int(w.correct_count)) > 0
    ]


@router.get("/api/insights")
def get_insights(db: Session = Depends(get_db)):
    """Real learning statistics + FSRS high-risk words + weak words."""
    return {
        "last_7_days": _last_7_days(db),
        "high_risk_words": _high_risk_words(db),
        "weak_words": _weak_words(db),
    }


@router.get("/api/confusion")
def list_confusion_sets(db: Session = Depends(get_db)):
    """List all confusion sets (built-in + AI-generated)."""
    sets = db.query(ConfusionSet).order_by(ConfusionSet.id.asc()).all()
    return {
        "sets": [
            {
                "id": c.id,
                "word_a": c.word_a,
                "word_b": c.word_b,
                "distinction_cn": c.distinction_cn,
                "memory_tip_cn": c.memory_tip_cn,
                "example_en": c.example_en,
                "example_cn": c.example_cn,
                "mastered": bool(c.mastered),
                "source": c.source,
            }
            for c in sets
        ]
    }


@router.post("/api/confusion/{set_id}/toggle")
def toggle_confusion_mastered(set_id: int, db: Session = Depends(get_db)):
    """Mark a confusion set as mastered / not-mastered."""
    row = db.query(ConfusionSet).filter(ConfusionSet.id == set_id).first()
    if not row:
        return {"error": "Confusion set not found"}
    row.mastered = not row.mastered
    db.commit()
    return {"id": set_id, "mastered": bool(row.mastered)}


@router.post("/api/ai/insights")
async def ai_insights(db: Session = Depends(get_db)):
    """AI interpretation of the real, DB-computed statistics (never fabricates)."""
    from ai.gateway import chat_completion, is_configured

    stats = _last_7_days(db)
    weak = _weak_words(db, limit=8)

    if stats["reviews"] == 0:
        return {
            "ai_available": False,
            "insight": "还没有足够的学习数据。开始学习后，这里会根据真实数据生成个性化洞察。",
            "highlights": [],
            "insufficient_data": True,
        }

    if not is_configured():
        return {
            "ai_available": False,
            "insight": "",
            "highlights": [],
            "insufficient_data": False,
        }

    weak_text = "、".join(f"{w['english']}(错{w['wrong_count']}次)" for w in weak) or "无"
    prompt = (
        "你是英语学习数据分析师。以下是学生过去 7 天的真实学习数据，请只基于这些数据给出洞察，"
        "不要编造任何数字：\n"
        f"- 学习单词：{stats['words_studied']}\n"
        f"- 复习次数：{stats['reviews']}\n"
        f"- 平均正确率：{int(stats['avg_accuracy'] * 100)}%\n"
        f"- 遗忘率：{int(stats['forgetting_rate'] * 100)}%\n"
        f"- 学习时长：{stats['minutes']} 分钟\n"
        f"- 活跃天数：{stats['days_active']}\n"
        f"- 薄弱词：{weak_text}\n\n"
        "只输出一个 JSON 对象："
        '{"insight":"一段中文洞察（1-2句，引用真实数据）","highlights":["要点1","要点2","要点3"]}'
    )

    result = await chat_completion(
        [
            {"role": "system", "content": "你只输出符合要求的纯 JSON，不要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=500,
        timeout=30,
    )

    if result.get("content") is None:
        return {"ai_available": False, "insight": "", "highlights": [], "insufficient_data": False}

    import json as _json
    import re as _re
    raw = result["content"]
    try:
        data = _json.loads(raw)
    except Exception:
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        data = _json.loads(m.group(0)) if m else {}

    return {
        "ai_available": True,
        "insight": str(data.get("insight", "") or "").strip(),
        "highlights": data.get("highlights", []) or [],
        "insufficient_data": False,
    }
