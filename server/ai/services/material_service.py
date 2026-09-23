"""Material Engine service — turn raw text into a candidate vocabulary list.

Pipeline:
    text → clean → tokenize → AI analysis (validated JSON) → candidate words
           ↘ (AI unavailable) local frequency-based fallback

The AI returns structured, schema-validated words; the local fallback guarantees
the feature still works offline (with a clear "heuristic, not AI" flag).
"""

import logging
import re
from collections import Counter

from ..gateway import chat_json
from ..schemas import MaterialAnalysis, ExtractedWord

logger = logging.getLogger(__name__)

# Common function words the Material Engine ignores when counting candidates.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "so", "for", "nor", "yet",
    "of", "to", "in", "on", "at", "by", "with", "from", "as", "into",
    "about", "over", "under", "between", "through", "during", "before",
    "after", "above", "below", "up", "down", "out", "off", "than", "then",
    "is", "are", "was", "were", "be", "been", "being", "am", "do", "does",
    "did", "have", "has", "had", "having", "will", "would", "shall", "should",
    "can", "could", "may", "might", "must", "it", "its", "this", "that",
    "these", "those", "i", "you", "he", "she", "we", "they", "them", "his",
    "her", "their", "our", "your", "my", "me", "us", "him", "who", "whom",
    "which", "what", "when", "where", "why", "how", "not", "no", "yes",
    "if", "else", "because", "although", "while", "since", "until", "also",
    "too", "very", "just", "only", "such", "both", "each", "every", "some",
    "any", "more", "most", "other", "another", "own", "same", "there", "here",
    "one", "two", "three", "get", "got", "make", "made", "take", "took",
    "say", "said", "see", "saw", "use", "used", "way", "day", "year", "time",
    "thing", "people", "man", "woman", "child", "world", "life", "work",
    "new", "good", "great", "many", "much", "little", "few", "first", "last",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'\-]{2,}")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip Markdown link/image/charset syntax."""
    if not text:
        return ""
    # Drop code fences, links [x](url), images ![x](url), and inline backticks.
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`#*_>~]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Extract lowercase candidate words, dropping stopwords and non-words."""
    words = _WORD_RE.findall(text.lower())
    return [w for w in words if w not in _STOPWORDS]


def extract_candidates_local(text: str, max_words: int = 20) -> list[ExtractedWord]:
    """Heuristic fallback: most frequent non-stopword tokens, no AI.

    Used when AI is unavailable so the feature still works; the UI flags these
    as "本地识别（非 AI）".
    """
    cleaned = clean_text(text)
    counter = Counter(tokenize(cleaned))
    candidates = []
    for word, freq in counter.most_common(max_words):
        importance = 5 if freq >= 4 else (4 if freq >= 3 else (3 if freq >= 2 else 2))
        candidates.append(ExtractedWord(
            word=word,
            meaning="",
            importance=importance,
            difficulty=3,
            reason=f"在文中出现 {freq} 次（本地频率识别）",
            example="",
            source_sentence="",
        ))
    return candidates


async def analyze_material(text: str, max_words: int = 30) -> MaterialAnalysis | None:
    """AI-analyze a material and return validated candidate words (or None)."""
    cleaned = clean_text(text)
    if not cleaned:
        return None

    # Cap the text sent to the model: enough context, no oversized payloads.
    context = cleaned[:6000]

    prompt = (
        "你是一名英语词汇教学专家。下面是一篇英语学习材料。请从中挑选最值得学习的"
        f"重点词汇（最多 {max_words} 个），优先挑选：\n"
        "1. 考试高频词、学术词、对理解文章关键的重要词；\n"
        "2. 忽略 the/have/very 这类功能词和过于基础的词；\n"
        "3. 尽量给出一个符合难度的自然例句（英文）。\n\n"
        "对每个词只输出一个 JSON 对象（不要输出 markdown 代码块），字段如下：\n"
        '{"word":"单词","meaning":"中文释义","importance":1到5的整数,'
        '"difficulty":1到5的整数,"reason":"为什么值得学（中文一句话）",'
        '"example":"一个自然简洁的英文例句","source_sentence":"原文中出现该词的句子"}\n\n'
        '请用 JSON 数组输出：{"words":[ {...}, {...} ]}\n'
        f"材料原文：\n{context}"
    )

    result = await chat_json(
        [
            {"role": "system", "content": "你只输出符合要求的纯 JSON，不要任何解释或 markdown。"},
            {"role": "user", "content": prompt},
        ],
        MaterialAnalysis,
        temperature=0.3,
        max_tokens=2500,
        timeout=60,
        retries=1,
    )

    if result is None:
        logger.warning("Material AI analysis failed; returning None for caller fallback")
        return None

    # De-duplicate by word, keep highest importance.
    seen: dict[str, ExtractedWord] = {}
    for w in result.words:
        key = w.word.lower()
        existing = seen.get(key)
        if existing is None or w.importance > existing.importance:
            seen[key] = w
    result.words = list(seen.values())
    return result
