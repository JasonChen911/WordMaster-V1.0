"""AI exercise generator — targeted practice for weak words.

Types: multiple_choice (选释义), spelling (拼写), fill_blank (语境填空),
discrimination (易混词辨析), listening (听音识词 — frontend uses TTS).
AI is called only when generating new content, never during normal review.
"""

import logging

from ..gateway import chat_json, is_configured
from ..schemas import ExerciseSet, ExerciseQuestion

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ("multiple_choice", "spelling", "fill_blank", "discrimination")


def fallback_questions(words: list[dict], exercise_type: str, count: int) -> list[ExerciseQuestion]:
    """Deterministic offline fallback so exercise generation never hard-fails."""
    questions = []
    for w in words[:count]:
        english = w.get("english", w.get("word", ""))
        chinese = w.get("chinese", w.get("meaning", ""))
        if exercise_type == "spelling":
            questions.append(ExerciseQuestion(
                type="spelling",
                question=f"请拼写「{chinese or english}」对应的英文单词",
                answer=english,
                explanation=f"正确答案是 {english}。",
                target_words=[english],
            ))
        elif exercise_type == "fill_blank":
            questions.append(ExerciseQuestion(
                type="fill_blank",
                question=f"语境填空：The key ___ (释义：{chinese}) is practice.",
                answer=english,
                explanation=f"此处应填 {english}。",
                target_words=[english],
            ))
        else:
            options = [chinese, *[x.get("chinese", "") for x in words if x.get("chinese") != chinese][:3]]
            while len(options) < 2:
                options.append("")
            import random
            random.shuffle(options)
            answer_idx = options.index(chinese) if chinese in options else 0
            questions.append(ExerciseQuestion(
                type="multiple_choice",
                question=f"「{english}」的中文意思是？",
                options=options[:4],
                answer=chr(65 + answer_idx),
                explanation=f"{english} 的意思是「{chinese}」。",
                target_words=[english],
            ))
    return questions


async def generate_exercises(words: list[dict], exercise_type: str = "multiple_choice", count: int = 5) -> dict:
    """Generate exercises targeting the given (weak) words."""
    if not words:
        return {"questions": [], "exercise_type": exercise_type, "ai_available": False}

    if exercise_type not in SUPPORTED_TYPES:
        exercise_type = "multiple_choice"

    if not is_configured():
        return {
            "questions": [q.model_dump() for q in fallback_questions(words, exercise_type, count)],
            "exercise_type": exercise_type,
            "ai_available": False,
        }

    words_text = "\n".join(
        f"- {w.get('english', w.get('word', ''))} = {w.get('chinese', w.get('meaning', ''))}"
        for w in words[:15]
    )

    type_instructions = {
        "multiple_choice": "为每个词出一道「选择正确中文释义」的选择题，4 个选项（A-D），answer 填正确选项字母。",
        "spelling": "为每个词出一道「根据中文拼写英文」的题，answer 填英文单词。",
        "fill_blank": "为每个词出一道「语境填空」题，句子留空 ___，answer 填英文单词，并在 explanation 里说明。",
        "discrimination": "为每对易混词出一道「辨析」题（选择填空），answer 填正确单词。",
    }

    prompt = (
        f"你是英语练习设计专家。用下面的单词设计 {count} 道练习题。\n\n"
        f"单词列表：\n{words_text}\n\n"
        f"题型：{type_instructions.get(exercise_type, '')}\n"
        "只输出一个 JSON 对象：\n"
        '{"questions":[{"type":"题型","question":"题干","options":["A. ...","B. ..."],'
        '"answer":"正确答案","explanation":"中文解析","difficulty":2,"target_words":["词"]}]}'
    )

    result = await chat_json(
        [
            {"role": "system", "content": "你只输出符合要求的纯 JSON 数组，不要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        ExerciseSet,
        temperature=0.6,
        max_tokens=1500,
        timeout=45,
        retries=1,
    )

    if result is None or not result.questions:
        return {
            "questions": [q.model_dump() for q in fallback_questions(words, exercise_type, count)],
            "exercise_type": exercise_type,
            "ai_available": False,
        }

    return {
        "questions": [q.model_dump() for q in result.questions[:count]],
        "exercise_type": exercise_type,
        "ai_available": True,
    }
