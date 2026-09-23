"""Teacher MVP routes — Local Classroom Demo.

Demo data is always flagged ``is_demo`` and clearly labelled in the UI; it is
never presented as real user data. Course creation reuses the Material Engine
so a teacher's workflow (upload → AI extract → confirm → course book) is real.
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models import Course, Student, StudentWordStat, Book
from core import _get_active_book_id

logger = logging.getLogger(__name__)

router = APIRouter()


def _class_stats(db: Session) -> dict:
    """Aggregate class-level statistics from (demo) students + word stats."""
    students = db.query(Student).all()
    if not students:
        return {
            "student_count": 0,
            "completion_rate": 0.0,
            "avg_accuracy": 0.0,
            "total_reviews": 0,
            "forgetting_rate": 0.0,
        }

    total_reviews = sum(s.total_reviews or 0 for s in students)
    total_correct = sum(s.correct_count or 0 for s in students)
    total_lapses = sum(s.lapses or 0 for s in students)
    completion = sum(
        (s.words_mastered or 0) / max(1, (s.words_studied or 0))
        for s in students
    ) / len(students)

    return {
        "student_count": len(students),
        "completion_rate": round(completion, 3),
        "avg_accuracy": round(total_correct / total_reviews, 3) if total_reviews else 0.0,
        "total_reviews": total_reviews,
        "forgetting_rate": round(total_lapses / total_reviews, 3) if total_reviews else 0.0,
    }


def _class_weak_words(db: Session, limit: int = 12) -> list[dict]:
    """Words with the most aggregated wrong answers / lapses across the class."""
    rows = (
        db.query(
            StudentWordStat.word,
            sa_func.sum(StudentWordStat.wrong_count).label("wrong"),
            sa_func.sum(StudentWordStat.lapses).label("lapses"),
            sa_func.count(StudentWordStat.student_id).label("students"),
        )
        .group_by(StudentWordStat.word)
        .order_by(sa_func.sum(StudentWordStat.wrong_count).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "word": word,
            "wrong_count": int(wrong or 0),
            "lapses": int(lapses or 0),
            "students": int(students or 0),
        }
        for word, wrong, lapses, students in rows
    ]


@router.get("/api/teacher/overview")
def teacher_overview(db: Session = Depends(get_db)):
    """Courses + demo class with real, DB-computed class statistics."""
    courses = [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description or "",
            "is_demo": bool(c.is_demo),
            "book_id": c.book_id,
        }
        for c in db.query(Course).order_by(Course.is_demo.asc(), Course.id.asc()).all()
    ]

    demo_students = [
        {
            "id": s.id,
            "name": s.name,
            "words_studied": s.words_studied or 0,
            "words_mastered": s.words_mastered or 0,
            "total_reviews": s.total_reviews or 0,
            "correct_count": s.correct_count or 0,
            "lapses": s.lapses or 0,
        }
        for s in db.query(Student).order_by(Student.id.asc()).all()
    ]

    return {
        "courses": courses,
        "is_demo": True,
        "demo_class_name": (db.query(Student).first().class_name if db.query(Student).first() else "Demo Class"),
        "class_stats": _class_stats(db),
        "class_weak_words": _class_weak_words(db),
        "students": demo_students,
    }


@router.post("/api/teacher/courses")
async def teacher_create_course(request: Request, db: Session = Depends(get_db)):
    """Create a course, optionally linking the currently-active word book."""
    try:
        body = await request.json()
    except Exception:
        return {"error": "请求体不是合法 JSON。"}

    name = str(body.get("name") or "").strip()
    if not name:
        return {"error": "课程名称不能为空。"}

    description = str(body.get("description") or "").strip()
    book_id = body.get("book_id")

    # If no explicit book_id, link the active book when it exists.
    if not book_id:
        book_id = _get_active_book_id(db) or None

    course = Course(name=name, description=description, book_id=book_id, is_demo=False)
    db.add(course)
    db.commit()
    db.refresh(course)

    return {"success": True, "course_id": course.id, "name": course.name, "is_demo": False}


@router.post("/api/teacher/report")
async def teacher_report(db: Session = Depends(get_db)):
    """AI teaching summary based on the real, DB-computed class statistics."""
    from ai.gateway import chat_completion, is_configured

    stats = _class_stats(db)
    weak = _class_weak_words(db, limit=8)

    if stats["student_count"] == 0:
        return {"ai_available": False, "summary": "班级暂无学生数据。"}

    weak_text = "、".join(f"{w['word']}(共错{w['wrong_count']}次,{w['students']}人)" for w in weak) or "无"

    if not is_configured():
        return {
            "ai_available": False,
            "summary": "",
            "weak_points": [w["word"] for w in weak],
            "suggestions": [],
        }

    prompt = (
        "你是一名英语教学顾问。以下是班级的真实学习数据，请只基于这些数据生成教学总结，"
        "不要编造数字：\n"
        f"- 学生数：{stats['student_count']}\n"
        f"- 平均完成率：{int(stats['completion_rate'] * 100)}%\n"
        f"- 平均正确率：{int(stats['avg_accuracy'] * 100)}%\n"
        f"- 遗忘率：{int(stats['forgetting_rate'] * 100)}%\n"
        f"- 共性薄弱词：{weak_text}\n\n"
        "只输出一个 JSON 对象："
        '{"summary":"一段中文教学总结（1-2句，引用真实数据）",'
        '"weak_points":["薄弱词1","薄弱词2"],'
        '"suggestions":["教学建议1","教学建议2","教学建议3"]}'
    )

    result = await chat_completion(
        [
            {"role": "system", "content": "你只输出符合要求的纯 JSON，不要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=600,
        timeout=30,
    )

    if result.get("content") is None:
        return {"ai_available": False, "summary": "", "weak_points": [], "suggestions": []}

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
        "summary": str(data.get("summary", "") or "").strip(),
        "weak_points": data.get("weak_points", []) or [],
        "suggestions": data.get("suggestions", []) or [],
    }
