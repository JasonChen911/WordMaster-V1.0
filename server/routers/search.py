"""Search and favorites routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Word, Book, DictionaryEntry
from schemas import WordOut

router = APIRouter()


@router.get("/api/search")
def search_words(
    q: str = Query("", min_length=0),
    db: Session = Depends(get_db),
):
    """Search words in SQLite by english or chinese."""
    if not q.strip():
        return {"words": [], "total": 0}

    words = (
        db.query(Word)
        .filter(
            (Word.english.ilike(f"%{q}%")) | (Word.chinese.ilike(f"%{q}%"))
        )
        .order_by(Word.english.asc())
        .limit(20)
        .all()
    )

    return {
        "words": [
            {
                "id": w.id,
                "english": w.english,
                "phonetic": w.phonetic or "",
                "chinese": w.chinese or "",
                "example_en": w.example_en or "",
                "example_cn": w.example_cn or "",
                "illustration": w.illustration or "",
                "difficulty": w.difficulty or 2.5,
                "is_favorite": bool(w.is_favorite),
                "is_mastered": bool(w.is_mastered),
                "review_count": w.review_count or 0,
                "study_status": w.study_status or "new",
                "accuracy_rate": w.accuracy_rate or 0.0,
                "proficiency": w.proficiency or 0,
            }
            for w in words
        ],
        "total": len(words),
    }


@router.get("/api/favorites", response_model=list[WordOut])
def get_favorites(db: Session = Depends(get_db)):
    return (
        db.query(Word)
        .filter(Word.is_favorite == True)
        .order_by(Word.english.asc())
        .all()
    )


@router.get("/api/search/all")
def search_all(
    q: str = Query("", min_length=1),
    book_id: int = Query(None, description="Dictionary book ID"),
    db: Session = Depends(get_db),
):
    """Search both study words and dictionary simultaneously (book-aware)."""
    if not q.strip():
        return {"study_words": [], "dictionary_results": [], "total": 0, "active_book": None}

    # Determine active book
    if book_id is None:
        active = db.query(Book).filter(Book.is_active == True).first()
        book_id = active.id if active else 0

    active_book = db.query(Book).filter(Book.id == book_id).first()

    # Search study words
    study_words = (
        db.query(Word)
        .filter(
            (Word.english.ilike(f"%{q}%")) | (Word.chinese.ilike(f"%{q}%"))
        )
        .order_by(Word.english.asc())
        .limit(20)
        .all()
    )

    # Search dictionary (scoped to active book)
    dict_query = db.query(DictionaryEntry).filter(
        (DictionaryEntry.word.ilike(f"%{q}%"))
        | (DictionaryEntry.definition_cn.ilike(f"%{q}%"))
        | (DictionaryEntry.definition_en.ilike(f"%{q}%"))
    )
    if book_id > 0:
        dict_query = dict_query.filter(DictionaryEntry.book_id == book_id)
    dict_results = dict_query.order_by(DictionaryEntry.word.asc()).limit(30).all()

    return {
        "study_words": [
            {
                "id": w.id,
                "english": w.english,
                "phonetic": w.phonetic,
                "chinese": w.chinese,
                "example_en": w.example_en,
                "example_cn": w.example_cn,
                "is_favorite": w.is_favorite,
                "is_mastered": w.is_mastered,
                "proficiency": w.proficiency,
            }
            for w in study_words
        ],
        "dictionary_results": [
            {
                "id": d.id,
                "word": d.word,
                "phonetic": d.phonetic,
                "definition": (d.definition_cn or d.definition_en or "")[:300],
                "example": d.example,
                "source": d.source,
                "book_id": d.book_id,
            }
            for d in dict_results
        ],
        "total": len(study_words) + len(dict_results),
        "active_book": {
            "id": active_book.id,
            "book_name": active_book.book_name,
            "word_count": active_book.word_count,
        } if active_book else None,
    }
