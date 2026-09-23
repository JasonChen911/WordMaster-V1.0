"""Reading → vocabulary → FSRS loop.

When a user clicks a word while reading, it is added to the active book's study
queue with its source document and original sentence recorded, so the word can
later be reviewed in its real context.
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Word, Book, SourceDocument, SourceWord
from core import _get_active_book_id, _link_book_words
from learning_events import log_event

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/reading/add-word")
async def reading_add_word(request: Request, db: Session = Depends(get_db)):
    """Add a word encountered while reading into the study queue with source context."""
    try:
        body = await request.json()
    except Exception:
        return {"error": "请求体不是合法 JSON。"}

    word_text = str(body.get("word") or "").strip().lower()
    if not word_text:
        return {"error": "缺少单词。"}

    meaning = str(body.get("meaning") or "").strip()
    example = str(body.get("example") or "").strip()
    source_title = str(body.get("source_document") or "").strip() or "阅读材料"
    source_sentence = str(body.get("source_sentence") or "").strip()

    # Find or create the study word (never overwrite existing progress fields).
    word = db.query(Word).filter(Word.english == word_text).first()
    if not word:
        word = Word(english=word_text, phonetic="", chinese=meaning or "", example_en=example or "", example_cn="")
        db.add(word)
        db.flush()
    else:
        if not word.chinese and meaning:
            word.chinese = meaning
        if not word.example_en and example:
            word.example_en = example

    # Find or create the source document.
    doc = db.query(SourceDocument).filter(SourceDocument.title == source_title).first()
    if not doc:
        doc = SourceDocument(title=source_title)
        db.add(doc)
        db.flush()

    # Record the source sentence (first occurrence wins).
    existing = (
        db.query(SourceWord)
        .filter(SourceWord.word_id == word.id, SourceWord.source_document_id == doc.id)
        .first()
    )
    if not existing:
        db.add(SourceWord(word_id=word.id, source_document_id=doc.id, source_sentence=source_sentence))

    # Link the word to the active book so it enters the FSRS study queue.
    bid = _get_active_book_id(db)
    if bid:
        _link_book_words(db, bid, [(word.english, word.phonetic or "", word.chinese or "", word.example_en or "", word.example_cn or "")])

    # Record the reading-lookup behavior as a learning event.
    log_event(
        db,
        word_id=word.id,
        book_id=bid or 0,
        activity_type="reading_lookup",
        result="",
        source_type="reading",
        source_id=doc.id,
        user_answer=word.english,
    )

    db.commit()

    return {
        "success": True,
        "word_id": word.id,
        "english": word.english,
        "source_document": source_title,
        "source_sentence": source_sentence,
    }


@router.get("/api/words/{word_id}/source")
def word_source(word_id: int, db: Session = Depends(get_db)):
    """Return the first source context (document + sentence) for a word."""
    row = (
        db.query(SourceDocument.title, SourceWord.source_sentence)
        .join(SourceWord, SourceWord.source_document_id == SourceDocument.id)
        .filter(SourceWord.word_id == word_id)
        .order_by(SourceWord.id.asc())
        .first()
    )
    if not row:
        return {"found": False, "source_document": "", "source_sentence": ""}
    return {"found": True, "source_document": row[0], "source_sentence": row[1]}
