"""Mini-games word source route."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Word, Book
from core import (
    _get_active_book_id, _book_id_int, _book_id_str, _get_book_scoped_word_ids,
)

router = APIRouter()


@router.get("/api/games/words")
def get_games_words(
    count: int = Query(20, ge=5, le=50),
    book_id: str = Query(None, description="Book ID; uses active book if omitted"),
    db: Session = Depends(get_db),
):
    """Get words suitable for mini-games from the specified book.

    Returns words with non-empty example sentences when available,
    falling back to any word in the selected book.
    """
    if book_id:
        bid = _book_id_int(db, book_id)
    else:
        bid = _get_active_book_id(db)

    if not bid:
        return {"words": [], "book_name": "", "book_id": ""}

    word_ids = _get_book_scoped_word_ids(db, bid)
    if not word_ids:
        return {"words": [], "book_name": "", "book_id": book_id or ""}

    import random as _random
    rng = _random.Random()

    # Prefer words with example sentences for FillBlank game
    with_examples = (
        db.query(Word)
        .filter(Word.id.in_(word_ids), Word.example_en != "", Word.example_en.isnot(None))
        .all()
    )
    rng.shuffle(with_examples)

    # Fill with any words for Letter Scramble
    remaining = (
        db.query(Word)
        .filter(Word.id.in_(word_ids))
        .all()
    )
    rng.shuffle(remaining)

    # Merge: examples first, then deduplicate
    seen = set()
    merged = []
    for w in with_examples + remaining:
        if w.id not in seen:
            seen.add(w.id)
            merged.append(w)
        if len(merged) >= count:
            break

    book = db.query(Book).filter(Book.id == bid).first()

    return {
        "words": [
            {
                "id": w.id,
                "english": w.english,
                "chinese": w.chinese or "",
                "phonetic": w.phonetic or "",
                "example_en": w.example_en or "",
                "example_cn": w.example_cn or "",
            }
            for w in merged
        ],
        "book_name": book.book_name if book else "",
        "book_id": book_id or _book_id_str(db, bid),
    }
