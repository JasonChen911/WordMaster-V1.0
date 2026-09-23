"""AI routes: word explanation, error analysis, config, reading, chat, quiz, report."""

import logging
import json as json_module
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models import Word, StudyRecord, DailyStats, WordAIExplanation
from schemas import (
    AIExplainRequest, AIExplainOut,
    AIErrorAnalysisRequest, AIErrorAnalysisOut,
    WordExplainRequest, WordExplainResponse,
)
from ai_service import (
    explain_word, analyze_errors, is_configured as ai_is_configured,
    generate_quiz, generate_report, explain_word_detail, AI_MODEL,
    chat_completion, _strip_code_fence,
)
from config_manager import (
    get_config_status, set_deepseek_api_key, is_ai_configured,
)
from ai.services import get_example, analyze_word_struggle, generate_exercises

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/ai/explain", response_model=AIExplainOut)
async def ai_explain(req: AIExplainRequest):
    """Get AI-powered word explanation."""
    logger.info(f"AI explain requested for: {req.english}")
    result = await explain_word(req.english, req.chinese)
    return result


@router.post("/api/word/explain", response_model=WordExplainResponse)
async def word_explain(req: WordExplainRequest, db: Session = Depends(get_db)):
    """Get detailed AI explanation for a word, with SQLite caching."""
    word_text = req.word.strip().lower()
    logger.info(f"Word detail explain requested: {word_text}")

    # Check cache first
    cached = db.query(WordAIExplanation).filter(
        WordAIExplanation.word == word_text
    ).first()

    if cached:
        try:
            data = json_module.loads(cached.explanation)
            data["cached"] = True
            data["ai_available"] = True
            data["word"] = word_text
            logger.info(f"Cache hit for: {word_text}")
            return data
        except (json_module.JSONDecodeError, TypeError):
            logger.warning(f"Corrupted cache for {word_text}, regenerating")

    # Call AI
    result = await explain_word_detail(word_text)

    if result.get("ai_available"):
        # Save to cache
        try:
            cache_entry = WordAIExplanation(
                word=word_text,
                explanation=json_module.dumps(result, ensure_ascii=False),
            )
            db.add(cache_entry)
            db.commit()
            logger.info(f"Cached explanation for: {word_text}")
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to cache explanation for {word_text}: {e}")

    result["word"] = word_text
    result["cached"] = False
    return result


@router.post("/api/ai/analyze-errors", response_model=AIErrorAnalysisOut)
async def ai_analyze_errors(req: AIErrorAnalysisRequest):
    """Get AI analysis of frequently mistaken words."""
    logger.info(f"AI error analysis requested for {len(req.error_words)} words")
    result = await analyze_errors([w.model_dump() for w in req.error_words])
    return result


@router.get("/api/ai/config-status")
def ai_config_status():
    """Get current AI configuration status (key masked)."""
    return get_config_status()


@router.post("/api/ai/save-key")
async def ai_save_key(request: Request):
    """Save DeepSeek API key to user config."""
    body = await request.json()
    key = body.get("api_key", "").strip()
    if key:
        set_deepseek_api_key(key)
        return {"success": True, "message": "API Key 已保存"}
    else:
        set_deepseek_api_key("")
        return {"success": True, "message": "API Key 已清除"}


@router.post("/api/ai/test-connection")
async def ai_test_connection():
    """Test the DeepSeek API connection."""
    if not ai_is_configured():
        return {"success": False, "message": "AI 服务未配置，请先在 设置 → AI 服务 中配置 API Key。"}

    result = await chat_completion(
        [{"role": "user", "content": "Hi"}],
        max_tokens=5,
        timeout=10,
    )
    if result.get("content") is not None:
        return {"success": True, "message": "连接成功！DeepSeek API 正常。"}
    return {"success": False, "message": result.get("error") or "连接失败，请重试。"}


@router.post("/api/ai/generate-reading")
async def ai_generate_reading(request: Request):
    """Generate a personalized English reading article via DeepSeek."""
    if not ai_is_configured():
        return {"error": "AI 服务未配置，请先在 设置 → AI 服务 中配置 API Key。"}

    body = await request.json()
    exam = body.get("exam", "CET-4")
    level = body.get("level", "中等")
    topic = body.get("topic", "科技")
    words = body.get("words", 500)

    prompt = (
        f"你是一名专业英语阅读训练教师。请生成一篇英语阅读文章。\n"
        f"目标考试：{exam}\n难度：{level}\n主题：{topic}\n文章长度：约{words}词\n\n"
        "要求：\n1. 使用符合目标考试水平的词汇和语法\n"
        "2. 文章自然流畅，不要像机器生成\n3. 适合英语学习者阅读\n4. 不要出现中文\n\n"
        "请严格按以下JSON格式输出（只输出纯JSON，不要markdown代码块）：\n"
        '{"title":"文章标题","content":"文章正文","vocabulary":[{"word":"词","meaning":"中文释义","example":"英文例句"}],'
        '"questions":[{"question":"问题（英文）","options":["A.选项","B.选项","C.选项","D.选项"],"answer":"A","explanation":"中文解析：为什么选A，在原文哪里找到答案"}]}\n'
        "vocabulary包含5-8个重点词汇，questions包含3-5道阅读理解选择题，每道题都要有详细中文explanation。"
    )

    result = await chat_completion(
        [{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2500,
        timeout=90,
    )
    if result.get("content") is None:
        return {"error": result.get("error") or "AI 返回格式异常，请重试。"}

    raw = _strip_code_fence(result["content"])
    try:
        return json_module.loads(raw)
    except json_module.JSONDecodeError:
        return {"error": "AI 返回格式异常，请重试。"}


@router.post("/api/ai/chat")
async def ai_chat(request: Request):
    """AI Tutor chat endpoint. Uses DeepSeek API with the user's key."""
    if not ai_is_configured():
        return {"reply": "AI 服务未配置，请先在 设置 → AI 服务 中配置 API Key。"}

    body = await request.json()
    messages = body.get("messages", [])
    if not isinstance(messages, list) or not messages:
        return {"reply": "消息内容为空，请重新输入。"}

    result = await chat_completion(messages, temperature=0.7, max_tokens=800, timeout=30)
    if result.get("content") is None:
        return {"reply": result.get("error") or "抱歉，请稍后重试。"}
    return {"reply": result["content"]}


@router.get("/api/ai/status")
def ai_status():
    """Check if AI service is usable (user key or default credential)."""
    key_configured = ai_is_configured()
    return {
        "available": key_configured,
        "model": AI_MODEL if key_configured else None,
        "message": "AI 服务可用" if key_configured else "AI 服务未配置",
    }


@router.post("/api/ai/quiz")
async def ai_quiz(
    quiz_type: str = Query("multiple_choice", description="multiple_choice, fill_blank"),
    count: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Generate AI-powered quiz from the user's study words."""
    # Get words the user has studied
    words = (
        db.query(Word)
        .filter(Word.review_count > 0)
        .order_by(Word.accuracy_rate.asc())  # Prioritize weak words
        .limit(20)
        .all()
    )
    if not words:
        # Fallback: random words from word bank
        words = db.query(Word).order_by(sa_func.random()).limit(20).all()

    word_dicts = [{"english": w.english, "chinese": w.chinese} for w in words]
    result = await generate_quiz(word_dicts, quiz_type, count)
    return result


@router.post("/api/ai/report")
async def ai_report(db: Session = Depends(get_db)):
    """Generate a personalized AI learning report."""
    # Gather stats
    today_str = date.today().isoformat()
    daily = db.query(DailyStats).filter(DailyStats.date == today_str).first()
    total_mastered = db.query(Word).filter(Word.is_mastered == True).count()
    total_words = db.query(Word).count()
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

    # Error words
    error_words = (
        db.query(Word)
        .filter(Word.review_count >= 2, Word.accuracy_rate < 1.0)
        .order_by(Word.accuracy_rate.asc())
        .limit(10)
        .all()
    )

    stats = {
        "today_studied": daily.words_studied if daily else 0,
        "total_mastered": total_mastered,
        "total_words": total_words,
        "streak_days": streak,
        "overall_accuracy": overall_acc,
        "error_words": [
            {"english": w.english, "chinese": w.chinese, "wrong_count": w.review_count - int(w.correct_count)}
            for w in error_words if (w.review_count - int(w.correct_count)) > 0
        ],
    }

    result = await generate_report(stats)
    return result


@router.get("/api/ai/example")
async def ai_example(
    word: str = Query(...),
    level: str = Query("CET4"),
    force: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Level-aware AI example sentence (cached by word+level)."""
    return await get_example(db, word, level, force=force)


@router.post("/api/ai/word-analysis")
async def ai_word_analysis(request: Request, db: Session = Depends(get_db)):
    """AI diagnosis for a single struggling word, based on real review data."""
    try:
        body = await request.json()
    except Exception:
        return {"ai_available": False, "error": "请求体不是合法 JSON。"}

    word = (body.get("word") or "").strip()
    summary = body.get("summary") or {}
    if not word:
        return {"ai_available": False, "error": "缺少单词。"}

    # Enrich the summary with the real, DB-derived stats for this word.
    row = db.query(Word).filter(Word.english == word.lower()).first()
    if row is not None:
        summary = {
            "review_count": row.review_count or 0,
            "wrong_count": (row.review_count or 0) - int(row.correct_count or 0),
            "accuracy_rate": row.accuracy_rate or 0.0,
            "lapse_count": summary.get("lapse_count", 0),
            "confused_with": summary.get("confused_with", []),
        }

    result = await analyze_word_struggle(word, summary)
    result["word"] = word
    return result


@router.post("/api/ai/exercises")
async def ai_exercises(request: Request):
    """Generate targeted practice questions for weak words."""
    try:
        body = await request.json()
    except Exception:
        return {"questions": [], "ai_available": False}

    words = body.get("words") or []
    exercise_type = body.get("exercise_type") or "multiple_choice"
    count = int(body.get("count") or 5)
    return await generate_exercises(words, exercise_type, count)
