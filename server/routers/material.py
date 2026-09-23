"""Material Engine routes — analyze text → candidate words → build a word book.

The AI Material Engine is the competition centerpiece: a teacher uploads an
article, WordMaster AI extracts the key vocabulary, the user confirms, and a
new word book is generated that flows into the FSRS study loop.
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Book, DictionaryEntry
from core import _link_book_words
from ai.services import analyze_material, extract_candidates_local

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/material/analyze")
async def material_analyze(request: Request):
    """Analyze raw text and return candidate vocabulary (AI or local fallback)."""
    try:
        body = await request.json()
    except Exception:
        return {"error": "请求体不是合法 JSON。"}

    text = (body.get("text") or "").strip()
    if not text:
        return {"error": "内容为空，请粘贴或上传学习材料。"}

    max_words = int(body.get("max_words") or 30)

    ai_result = await analyze_material(text, max_words=max_words)
    if ai_result is not None and ai_result.words:
        return {
            "candidates": [w.model_dump() for w in ai_result.words],
            "document_summary": ai_result.document_summary,
            "ai_available": True,
            "source_text": text,
        }

    # AI unavailable or failed → local frequency fallback, clearly flagged.
    local = extract_candidates_local(text, max_words=max_words)
    return {
        "candidates": [w.model_dump() for w in local],
        "ai_available": False,
        "source_text": text,
        "note": "AI 服务不可用，已使用本地频率识别。可稍后在设置中配置 API Key 后重新分析。",
    }


@router.post("/api/material/import")
async def material_import(request: Request, db: Session = Depends(get_db)):
    """Create a new word book from user-confirmed candidates."""
    try:
        body = await request.json()
    except Exception:
        return {"error": "请求体不是合法 JSON。"}

    book_name = (body.get("book_name") or "").strip() or "AI 词书"
    words = body.get("words") or []
    if not isinstance(words, list) or not words:
        return {"error": "没有可导入的单词。"}

    # Build canonical study entries: (word, phonetic, chinese, example, example_cn)
    entries = []
    seen = set()
    for w in words:
        if not isinstance(w, dict):
            continue
        word = str(w.get("word") or "").strip().lower()
        if not word or word in seen:
            continue
        seen.add(word)
        meaning = str(w.get("meaning_zh") or w.get("meaning") or "").strip()
        example = str(w.get("example") or "").strip()
        entries.append((word, "", meaning, example, ""))

    if not entries:
        return {"error": "没有有效单词。"}

    book = Book(book_name=book_name, file_name=f"material.{len(entries)}", word_count=0, is_active=False)
    db.add(book)
    db.commit()
    db.refresh(book)

    for word, _phonetic, meaning, example, _cn in entries:
        db.add(DictionaryEntry(
            book_id=book.id,
            word=word,
            phonetic="",
            definition_cn=meaning,
            example=example,
            source="material",
        ))

    linked = _link_book_words(db, book.id, entries)
    book.word_count = len(entries)

    # Activate the newly created book so the user studies it immediately.
    from models import Book as _Book
    from sqlalchemy import text as _text
    db.query(_Book).update({_Book.is_active: False})
    book.is_active = True
    db.execute(
        _text("INSERT OR REPLACE INTO user_settings (key, value, updated_at) VALUES ('active_book', :val, datetime('now'))"),
        {"val": book_name},
    )

    db.commit()

    logger.info("Material import: book '%s' (id=%s) imported %s words", book_name, book.id, len(entries))
    return {
        "success": True,
        "book_id": book.id,
        "book_name": book_name,
        "imported": len(entries),
        "linked": linked,
    }
