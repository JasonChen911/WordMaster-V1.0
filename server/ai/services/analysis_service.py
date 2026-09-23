"""AI learning-diagnosis service.

Generates "为什么我总记不住它" explanations from *real* review data — never
fabricated stats. If there is not enough history, the caller shows a clear
"data insufficient" message instead of a made-up diagnosis.
"""

import logging

from ..gateway import chat_json, is_configured
from ..schemas import LearningAnalysis

logger = logging.getLogger(__name__)

MIN_HISTORY = 2  # minimum reviews before a meaningful diagnosis is possible


async def analyze_word_struggle(word_text: str, summary: dict) -> dict:
    """Return a diagnosis dict for one struggling word.

    ``summary`` must contain review_count, wrong_count, accuracy_rate,
    lapse_count and optionally confused_with (list of similar words).
    """
    review_count = int(summary.get("review_count") or 0)
    wrong_count = int(summary.get("wrong_count") or 0)

    if review_count < MIN_HISTORY:
        return {
            "ai_available": False,
            "diagnosis": "",
            "mistake_pattern": "",
            "suggestions": [],
            "practice_sentence": "",
            "insufficient_data": True,
        }

    if not is_configured():
        return {
            "ai_available": False,
            "diagnosis": "",
            "mistake_pattern": "",
            "suggestions": [],
            "practice_sentence": "",
            "insufficient_data": False,
        }

    confused = summary.get("confused_with") or []
    confused_text = "、".join(confused) if confused else "无"

    prompt = (
        f"你是英语学习诊断专家。学生反复记不住单词 \"{word_text}\"，以下是他的真实学习数据：\n"
        f"- 复习次数：{review_count}\n"
        f"- 答错次数：{wrong_count}\n"
        f"- 正确率：{round((summary.get('accuracy_rate') or 0) * 100)}%\n"
        f"- 遗忘（忘记）次数：{summary.get('lapse_count') or 0}\n"
        f"- 经常与之混淆的词：{confused_text}\n\n"
        "请基于这些真实数据诊断他记不住这个词的可能原因，并给出可操作的建议。\n"
        "只输出一个 JSON 对象：\n"
        '{"diagnosis":"中文诊断（2-3句，基于数据）",'
        '"mistake_pattern":"错误模式（如拼写/选义/易混）",'
        '"suggestions":["建议1","建议2","建议3"],'
        '"practice_sentence":"一个用于巩固该词的练习填空句（英文，留空用 ___）"}'
    )

    result = await chat_json(
        [
            {"role": "system", "content": "你只输出符合要求的纯 JSON，不要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        LearningAnalysis,
        temperature=0.5,
        max_tokens=600,
        timeout=30,
        retries=1,
    )

    if result is None:
        return {
            "ai_available": False,
            "diagnosis": "",
            "mistake_pattern": "",
            "suggestions": [],
            "practice_sentence": "",
            "insufficient_data": False,
        }

    return {
        "ai_available": True,
        "diagnosis": result.diagnosis,
        "mistake_pattern": result.mistake_pattern,
        "suggestions": result.suggestions,
        "practice_sentence": result.practice_sentence,
        "insufficient_data": False,
    }
