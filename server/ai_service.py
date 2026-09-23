"""AI service module for WordMaster.

Provides:
- Word explanation (root analysis, memory tips)
- Word detail explanation (POS, meaning, example sentence + translation)
- Error word analysis
- Quiz generation (multiple choice, fill-in-blank)
- Learning report generation
- A single, shared chat-completion helper used by every DeepSeek caller.
"""

import json
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Runtime config — resolved from config_manager (env vars → config.json → default).
AI_TIMEOUT = float(os.environ.get("AI_TIMEOUT", "30"))
AI_MODEL = os.environ.get("AI_MODEL", "deepseek-chat")


def _get_api_key() -> str:
    """Resolve the API key via the single config entry point (config_manager)."""
    try:
        from config_manager import get_deepseek_api_key
        return get_deepseek_api_key()
    except Exception:
        return ""


def _get_api_base() -> str:
    """Resolve and normalize the API base URL from config_manager."""
    try:
        from config_manager import get_deepseek_api_base
        return (get_deepseek_api_base() or "https://api.deepseek.com/v1").rstrip("/")
    except Exception:
        return "https://api.deepseek.com/v1"


def build_chat_url() -> str:
    """Return the full chat/completions endpoint URL."""
    return f"{_get_api_base()}/chat/completions"


def is_configured() -> bool:
    """Check if AI service has a valid API key configured."""
    key = _get_api_key()
    return bool(key) and len(key) > 10


# ─────────────────────────────────────────────────────────────────
#  JSON parsing helpers
# ─────────────────────────────────────────────────────────────────

def _strip_code_fence(raw: str) -> str:
    """Remove Markdown code fences (```json ... ```) from a model response."""
    text = raw.strip()
    if not text.startswith("```"):
        return text
    # Remove the opening fence line (``` or ```json)
    lines = text.split("\n")
    # drop opening fence
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    # drop trailing closing fence
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_json_response(raw: Optional[str], fallback):
    """Parse JSON from an AI response, handling markdown code fences and stray text."""
    if raw is None:
        return fallback
    try:
        clean = _strip_code_fence(raw)
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Fallback: find the first JSON object/array in the text.
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", raw):
        try:
            value, _ = decoder.raw_decode(raw, match.start())
            return value
        except json.JSONDecodeError:
            continue

    logger.warning(f"AI returned non-JSON: {raw[:200]}")
    return fallback


# ─────────────────────────────────────────────────────────────────
#  Shared chat completion
# ─────────────────────────────────────────────────────────────────

async def chat_completion(
    messages: list[dict],
    *,
    temperature: float = 0.7,
    max_tokens: int = 800,
    timeout: float | None = None,
) -> dict:
    """Send one chat-completion request and return a normalized result dict.

    Returns:
        {"content": str|None, "error": str|None, "status": int|None}
    Exactly one of ``content`` / ``error`` is populated on success / failure.
    """
    if not is_configured():
        return {
            "content": None,
            "error": "AI 服务未配置，请先在 设置 → AI 服务 中配置 API Key。",
            "status": None,
        }

    api_key = _get_api_key()
    url = build_chat_url()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    effective_timeout = timeout if timeout is not None else AI_TIMEOUT

    try:
        async with httpx.AsyncClient(timeout=effective_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices") or []
                content = ""
                if choices:
                    content = (choices[0].get("message") or {}).get("content") or ""
                content = content.strip()
                if not content:
                    return {"content": None, "error": "AI 返回了空内容，请重试。", "status": 200}
                return {"content": content, "error": None, "status": 200}

            status = resp.status_code
            if status == 401:
                return {"content": None, "error": "API Key 无效，请检查设置。", "status": status}
            if status == 402:
                return {"content": None, "error": "API 余额不足，请充值。", "status": status}
            if status == 429:
                return {"content": None, "error": "请求过于频繁，请稍后重试。", "status": status}
            if status >= 500:
                return {"content": None, "error": f"DeepSeek 服务暂时不可用 (HTTP {status})，请稍后重试。", "status": status}
            return {"content": None, "error": f"API 错误 (HTTP {status})，请稍后重试。", "status": status}

    except httpx.TimeoutException:
        logger.error(f"AI API timeout after {effective_timeout}s")
        return {"content": None, "error": f"请求超时（>{effective_timeout} 秒），请稍后重试。", "status": None}
    except httpx.ConnectError:
        logger.error("AI API connection error")
        return {"content": None, "error": "无法连接到 API 服务器，请检查网络。", "status": None}
    except Exception as e:  # noqa: BLE001 — surface a friendly message, log the detail
        logger.error(f"AI API unexpected error: {type(e).__name__}: {e}")
        return {"content": None, "error": f"连接失败：{str(e)[:80]}", "status": None}


async def _chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 600,
    timeout: float | None = None,
) -> Optional[str]:
    """Compatibility wrapper returning just the content (or None)."""
    result = await chat_completion(
        messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout
    )
    return result.get("content")


# ─────────────────────────────────────────────────────────────────
#  Word Explanation
# ─────────────────────────────────────────────────────────────────

async def explain_word(english: str, chinese: str) -> dict:
    """Generate AI explanation for a word."""
    prompt = f"""You are an English vocabulary teacher. Explain the word "{english}" (Chinese meaning: {chinese}).

Respond in JSON format only, no markdown, with these fields:
- "simple_explanation_cn": A simple Chinese explanation (1-2 sentences)
- "word_root": Root/affix analysis in Chinese. If no clear root, say "无明显词根"
- "memory_tip": A creative memory tip in Chinese (1 sentence) to help remember this word
- "example_sentences": An array of 2 example sentences with translations. Each: {{"en": "...", "cn": "..."}}

IMPORTANT: Return ONLY valid JSON, no other text."""

    result = await chat_completion(
        [
            {"role": "system", "content": "You are a professional English teacher. Always respond in clean JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=600,
    )
    raw = result.get("content")

    if raw is None:
        return {
            "simple_explanation_cn": "",
            "word_root": "",
            "memory_tip": f"💡 将「{english}」拆分成音节记忆，结合例句加深印象。",
            "example_sentences": [],
            "ai_available": False,
        }

    data = _parse_json_response(raw, {})
    if not isinstance(data, dict):
        data = {}

    explanation_cn = str(data.get("simple_explanation_cn", "") or "").strip()
    word_root = str(data.get("word_root", "") or "").strip()
    memory_tip = str(data.get("memory_tip", "") or "").strip()
    examples = data.get("example_sentences") or []
    if not isinstance(examples, list):
        examples = []
    examples = [
        {"en": str(e.get("en", "") or "").strip(), "cn": str(e.get("cn", "") or "").strip()}
        for e in examples
        if isinstance(e, dict)
    ]

    return {
        "simple_explanation_cn": explanation_cn,
        "word_root": word_root,
        "memory_tip": memory_tip,
        "example_sentences": examples,
        "ai_available": bool(explanation_cn or word_root or memory_tip or examples),
    }


# ─────────────────────────────────────────────────────────────────
#  Word Detail Explanation (Study page inline AI example + meaning)
# ─────────────────────────────────────────────────────────────────

async def explain_word_detail(english: str) -> dict:
    """Generate a structured detailed explanation for a single word.

    Returns a dict with keys: pos, core_meaning, simple_understanding,
    example_en, example_cn, usage_tip, ai_available.
    """
    prompt = f"""You are a professional English teacher. Explain the English word "{english}" for a Chinese learner.

Return ONLY a JSON object (no markdown, no commentary) with exactly these fields:
- "pos": part of speech (e.g. "v." / "n." / "adj.")
- "core_meaning": the core Chinese meaning, no more than 20 characters
- "simple_understanding": a short, natural Chinese explanation (as if explaining to a friend)
- "example_en": one natural, learner-friendly English example sentence containing "{english}"
- "example_cn": the natural Chinese translation of example_en
- "usage_tip": one short Chinese sentence about when/how to use the word

IMPORTANT: Return ONLY valid JSON."""

    result = await chat_completion(
        [
            {"role": "system", "content": "你是一名专业的英语老师，擅长用简洁清晰的中文解释英语单词。只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=500,
    )
    raw = result.get("content")

    if raw is None:
        return {
            "pos": "", "core_meaning": "", "simple_understanding": "",
            "example_en": "", "example_cn": "", "usage_tip": "",
            "ai_available": False, "error": result.get("error"),
        }

    fields = _parse_explain_response(raw)
    ai_available = any(fields.get(k) for k in (
        "pos", "core_meaning", "simple_understanding", "example_en", "example_cn", "usage_tip"
    ))
    fields["ai_available"] = ai_available
    if not ai_available:
        fields["error"] = "AI 返回内容无法解析，请点击重试。"
    return fields


def _parse_explain_response(raw: str) -> dict:
    """Parse the AI explanation response (JSON first, then 【标记】 text)."""
    fields = {
        "pos": "",
        "core_meaning": "",
        "simple_understanding": "",
        "example_en": "",
        "example_cn": "",
        "usage_tip": "",
    }

    # ── Strategy 1: JSON object ──
    data = _parse_json_response(raw, None)
    if isinstance(data, dict):
        for key in fields:
            value = data.get(key)
            if isinstance(value, str):
                fields[key] = value.strip()
            elif value is not None:
                fields[key] = str(value).strip()
        if any(fields.values()):
            return fields

    # ── Strategy 2: 【label】 content markers ──
    label_map = {
        "词性": "pos",
        "核心释义": "core_meaning",
        "简单理解": "simple_understanding",
        "例句": "example_en",
        "中文": "example_cn",
        "使用提示": "usage_tip",
    }
    pattern = r"【(.+?)】\s*\n?\s*(.+?)(?=\n【|\Z)"
    matches = re.findall(pattern, raw, re.DOTALL)
    for label, content in matches:
        key = label_map.get(label.strip())
        if key:
            fields[key] = content.strip()

    if not any(fields.values()):
        current_key = None
        for line in raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            m = re.match(r"【(.+?)】", line)
            if m:
                label = m.group(1).strip()
                current_key = label_map.get(label)
                remaining = line[m.end():].strip()
                if remaining and current_key:
                    fields[current_key] = remaining
            elif current_key:
                if fields[current_key]:
                    fields[current_key] += "\n" + line
                else:
                    fields[current_key] = line

    return fields


# ─────────────────────────────────────────────────────────────────
#  Error Analysis
# ─────────────────────────────────────────────────────────────────

async def analyze_errors(error_words: list[dict]) -> dict:
    """Analyze user's frequently-mistaken words."""
    if not error_words:
        return {"analysis": "暂无错词数据，继续保持！", "weakness_patterns": [], "suggestions": [], "ai_available": False}

    words_text = "\n".join(
        f"- {w['english']} ({w['chinese']}): 错误{w['wrong_count']}次, 正确率{w['accuracy_rate']:.0%}"
        for w in error_words[:20]
    )

    prompt = f"""Analyze these frequently mistaken English words and provide study advice:

{words_text}

Respond in JSON format only:
- "analysis": Brief analysis in Chinese (2-3 sentences) of patterns in these errors
- "weakness_patterns": Array of 2-3 weakness patterns found (in Chinese)
- "suggestions": Array of 3 specific study tips (in Chinese)
Return ONLY valid JSON."""

    result = await chat_completion(
        [
            {"role": "system", "content": "You are an expert English learning analyst. Respond in clean JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    raw = result.get("content")

    if raw is None:
        return {
            "analysis": f"你有 {len(error_words)} 个薄弱词汇需要加强复习。",
            "weakness_patterns": [],
            "suggestions": ["每天花10分钟专门复习错词", "尝试用错词造句加深记忆", "将易混淆的单词整理成对比表"],
            "ai_available": False,
        }

    data = _parse_json_response(raw, {})
    if not isinstance(data, dict):
        data = {}
    return {
        "analysis": str(data.get("analysis", "") or "").strip(),
        "weakness_patterns": data.get("weakness_patterns", []) or [],
        "suggestions": data.get("suggestions", []) or [],
        "ai_available": True,
    }


# ─────────────────────────────────────────────────────────────────
#  Quiz Generation
# ─────────────────────────────────────────────────────────────────

async def generate_quiz(
    words: list[dict],
    quiz_type: str = "multiple_choice",
    count: int = 5,
) -> dict:
    """Generate AI-powered quiz questions."""
    if not words:
        return {"questions": [], "quiz_type": quiz_type, "ai_available": False}

    words_text = "\n".join(
        f"- {w.get('english', w.get('word', ''))} = {w.get('chinese', w.get('meaning', ''))}"
        for w in words[:20]
    )

    type_instructions = {
        "multiple_choice": """Generate multiple choice questions.
Format each: {{"question": "What is the Chinese meaning of 'word'?", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "A", "word": "word"}}""",
        "fill_blank": """Generate fill-in-the-blank questions with Chinese hints.
Format each: {{"sentence": "The ___ (公司) is growing fast.", "answer": "company", "hint": "公司", "word": "company"}}""",
    }

    instruction = type_instructions.get(quiz_type, type_instructions["multiple_choice"])

    prompt = f"""You are an English test generator. Using these words:

{words_text}

{instruction}

Generate exactly {count} questions.
Return ONLY a JSON array of questions, no markdown."""

    result = await chat_completion(
        [
            {"role": "system", "content": "You are an expert English test designer. Respond in clean JSON arrays only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
    )
    raw = result.get("content")

    if raw is None:
        return {
            "questions": _fallback_quiz(words, quiz_type, count),
            "quiz_type": quiz_type,
            "ai_available": False,
        }

    questions = _parse_json_response(raw, [])
    if isinstance(questions, dict):
        questions = questions.get("questions", [])
    if not isinstance(questions, list):
        questions = _fallback_quiz(words, quiz_type, count)

    return {
        "questions": questions[:count],
        "quiz_type": quiz_type,
        "ai_available": True,
    }


def _fallback_quiz(words: list[dict], quiz_type: str, count: int) -> list[dict]:
    """Generate simple fallback quiz without AI."""
    import random

    questions = []
    for i, w in enumerate(words[:count]):
        if quiz_type == "multiple_choice":
            distractors = [x.get('chinese', '') for j, x in enumerate(words) if j != i][:3]
            while len(distractors) < 3:
                distractors.append('')
            options = [w.get('chinese', ''), *distractors[:3]]
            random.shuffle(options)
            answer_idx = options.index(w.get('chinese', ''))
            questions.append({
                "question": f"「{w.get('english', w.get('word', ''))}」的中文意思是？",
                "options": [f"{chr(65+k)}. {v}" for k, v in enumerate(options)],
                "answer": chr(65 + answer_idx),
                "word": w.get('english', ''),
            })
        elif quiz_type == "fill_blank":
            questions.append({
                "sentence": f"请拼写「{w.get('chinese', '')}」对应的英文单词",
                "answer": w.get('english', w.get('word', '')),
                "hint": w.get('chinese', ''),
                "word": w.get('english', ''),
            })
    return questions


# ─────────────────────────────────────────────────────────────────
#  Learning Report
# ─────────────────────────────────────────────────────────────────

async def generate_report(stats: dict) -> dict:
    """Generate a personalized learning report."""
    if not is_configured():
        return {
            "summary": f"今日学习 {stats.get('today_studied', 0)} 个单词，连续 {stats.get('streak_days', 0)} 天打卡！",
            "strengths": ["保持每日学习习惯"],
            "improvements": ["建议配置 AI 以获取个性化分析"],
            "plan": ["继续按艾宾浩斯曲线复习"],
            "ai_available": False,
        }

    prompt = f"""Generate a Chinese learning report based on these stats:
- Today studied: {stats.get('today_studied', 0)} words
- Total mastered: {stats.get('total_mastered', 0)} / {stats.get('total_words', 0)}
- Streak: {stats.get('streak_days', 0)} days
- Overall accuracy: {stats.get('overall_accuracy', 0)}
- Weak words: {len(stats.get('error_words', []))}

Respond in JSON:
- "summary": 1-2 sentence encouraging summary in Chinese
- "strengths": array of 2 strengths
- "improvements": array of 2 areas to improve
- "plan": array of 3 specific next steps
Return ONLY valid JSON."""

    result = await chat_completion(
        [
            {"role": "system", "content": "You are an encouraging English learning coach. Respond in clean JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    raw = result.get("content")

    if raw is None:
        return {
            "summary": f"今日学习了 {stats.get('today_studied', 0)} 个单词，继续保持！",
            "strengths": ["坚持每日学习"],
            "improvements": ["增加复习频率"],
            "plan": ["每天复习前一天的单词", "完成每日学习任务"],
            "ai_available": False,
        }

    data = _parse_json_response(raw, {})
    if not isinstance(data, dict):
        data = {}
    return {
        "summary": str(data.get("summary", "") or "").strip(),
        "strengths": data.get("strengths", []) or [],
        "improvements": data.get("improvements", []) or [],
        "plan": data.get("plan", []) or [],
        "ai_available": True,
    }

