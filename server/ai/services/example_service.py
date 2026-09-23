"""AI example-sentence service with a level-aware content cache.

A word is generated once per (word, level, exam_type) and cached; re-generation
is user-triggered only. Supports 高中 / CET4 / CET6 / 考研 / TOEFL difficulty.
"""

import json
import logging

from sqlalchemy.orm import Session

from ..gateway import chat_completion, is_configured
from ..schemas import ExampleSentence
from models import AIContentCache

logger = logging.getLogger(__name__)

# Map a level key to a prompt directive about sentence difficulty.
LEVEL_PROMPTS = {
    "高中": "使用高中英语水平的基础词汇和简单句式，句子简短自然。",
    "CET4": "使用四级（CET-4）水平的词汇和句式，句子自然简洁。",
    "CET6": "使用六级（CET-6）水平词汇，可含一个从句，但不过于复杂。",
    "考研": "使用考研英语水平词汇，句式正式、书面。",
    "TOEFL": "使用托福水平词汇，贴近学术语境但保持清晰。",
}

# Map a level key to an example style hint.
EXAM_STYLE = {
    "CET4": "四级",
    "CET6": "六级",
    "考研": "考研",
    "TOEFL": "托福",
    "高中": "高中",
}

_CACHE_VERSION = "1"


def normalize_level(level: str) -> str:
    return level if level in LEVEL_PROMPTS else "CET4"


def _cache_key(word: str, level: str) -> str:
    return f"{word.lower()}::{normalize_level(level)}"


def get_cached_example(db: Session, word: str, level: str) -> ExampleSentence | None:
    """Return a cached example for (word, level), or None."""
    row = (
        db.query(AIContentCache)
        .filter(
            AIContentCache.word == word.lower(),
            AIContentCache.level == normalize_level(level),
            AIContentCache.content_type == "example",
        )
        .first()
    )
    if not row:
        return None
    try:
        data = json.loads(row.payload)
        return ExampleSentence(example_en=data.get("example_en", ""), example_cn=data.get("example_cn", ""))
    except Exception:
        return None


def _save_example(db: Session, word: str, level: str, sentence: ExampleSentence, model: str = ""):
    try:
        row = (
            db.query(AIContentCache)
            .filter(
                AIContentCache.word == word.lower(),
                AIContentCache.level == normalize_level(level),
                AIContentCache.content_type == "example",
            )
            .first()
        )
        payload = json.dumps(sentence.model_dump(), ensure_ascii=False)
        if row:
            row.payload = payload
            row.model = model
        else:
            db.add(AIContentCache(
                word=word.lower(),
                level=normalize_level(level),
                exam_type=EXAM_STYLE.get(normalize_level(level), "general"),
                content_type="example",
                payload=payload,
                model=model,
                version=_CACHE_VERSION,
            ))
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning("Failed to cache example: %s", e)


async def get_example(db: Session, word: str, level: str, *, force: bool = False) -> dict:
    """Return {"example_en", "example_cn", "cached", "ai_available"}.

    Serves from cache when present; otherwise generates via AI. ``force``
    regenerates even when cached.
    """
    word = word.strip().lower()
    level = normalize_level(level)

    if not force:
        cached = get_cached_example(db, word, level)
        if cached:
            return {
                "example_en": cached.example_en,
                "example_cn": cached.example_cn,
                "cached": True,
                "ai_available": True,
                "level": level,
            }

    if not is_configured():
        return {
            "example_en": "",
            "example_cn": "",
            "cached": False,
            "ai_available": False,
            "level": level,
            "error": "AI 服务未配置，无法生成例句。",
        }

    directive = LEVEL_PROMPTS[level]
    prompt = (
        f"请为英语单词 \"{word}\" 写一个例句（{directive}）。\n"
        "要求：\n"
        "1. 例句必须自然、简洁，真实体现该词的含义；\n"
        "2. 不得编造该词不存在的含义；\n"
        "3. 不得使用过于复杂的结构；\n"
        "4. 例句中必须包含目标词。\n\n"
        "只输出一个 JSON 对象："
        '{"example_en":"英文例句","example_cn":"中文翻译"}'
    )

    result = await chat_completion(
        [
            {"role": "system", "content": "你只输出符合要求的纯 JSON，不要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=300,
        timeout=30,
    )

    if result.get("content") is None:
        return {
            "example_en": "",
            "example_cn": "",
            "cached": False,
            "ai_available": False,
            "level": level,
            "error": result.get("error"),
        }

    # Reuse the gateway's lenient JSON extraction via a tiny inline parse.
    import re as _re
    raw = result["content"]
    try:
        import json as _json
        data = _json.loads(raw)
    except Exception:
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        if not m:
            return {"example_en": "", "example_cn": "", "cached": False, "ai_available": False, "level": level, "error": "AI 返回无法解析。"}
        try:
            data = _json.loads(m.group(0))
        except Exception:
            return {"example_en": "", "example_cn": "", "cached": False, "ai_available": False, "level": level, "error": "AI 返回无法解析。"}

    sentence = ExampleSentence(
        example_en=str(data.get("example_en", "") or "").strip(),
        example_cn=str(data.get("example_cn", "") or "").strip(),
    )
    if not sentence.example_en:
        return {"example_en": "", "example_cn": "", "cached": False, "ai_available": False, "level": level, "error": "AI 未返回有效例句。"}

    _save_example(db, word, level, sentence, model="")
    return {
        "example_en": sentence.example_en,
        "example_cn": sentence.example_cn,
        "cached": False,
        "ai_available": True,
        "level": level,
    }
