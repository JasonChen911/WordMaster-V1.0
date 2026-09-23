"""Book management routes: listing, activation, deletion, progress."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from database import get_db
from models import Book, BookWord, StudyRecord, DictionaryEntry, Word
from core import (
    BOOK_ID_MAP, _get_active_book_id, _book_id_int, _book_id_str,
    _get_book_scoped_word_ids, _get_progress_stats_sql,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/books")
def list_books(db: Session = Depends(get_db)):
    """List all books with their stats from SQLite."""
    books = db.query(Book).order_by(Book.id.asc()).all()
    active_id = _get_active_book_id(db)

    return {
        "books": [
            {
                "id": BOOK_ID_MAP.get(b.book_name, b.book_name),
                "book_name": b.book_name,
                "file_name": b.file_name or "",
                "word_count": b.word_count or 0,
                "is_active": b.id == active_id,
                "is_builtin": bool(b.is_builtin),
                "created_at": b.created_at.isoformat() if b.created_at else "",
            }
            for b in books
        ]
    }


@router.get("/api/books/active")
def get_active_book_route(db: Session = Depends(get_db)):
    """Get the currently active book from SQLite."""
    bid = _get_active_book_id(db)
    book = db.query(Book).filter(Book.id == bid).first()
    if not book:
        return {"book": None}
    return {
        "book": {
            "id": BOOK_ID_MAP.get(book.book_name, book.book_name),
            "book_name": book.book_name,
            "file_name": book.file_name or "",
            "word_count": book.word_count or 0,
            "is_active": True,
            "is_builtin": bool(book.is_builtin),
        }
    }


@router.post("/api/books/{book_id}/activate")
def activate_book(book_id: str, db: Session = Depends(get_db)):
    """Set a book as the active (current) book in SQLite."""
    bid = _book_id_int(db, book_id)
    book = db.query(Book).filter(Book.id == bid).first()

    # Deactivate all, activate target
    db.query(Book).update({Book.is_active: False})
    if book:
        book.is_active = True

    # Update user_settings
    db.execute(
        sa_text("INSERT OR REPLACE INTO user_settings (key, value, updated_at) VALUES ('active_book', :val, datetime('now'))"),
        {"val": book_id},
    )
    db.commit()

    logger.info(f"Activated book: {book_id} (SQLite id={bid})")
    return {
        "success": True,
        "book": {
            "id": book_id,
            "book_name": book.book_name if book else book_id,
            "word_count": book.word_count if book else 0,
        },
    }


@router.delete("/api/books/{book_id}")
def delete_book(book_id: str, db: Session = Depends(get_db)):
    """Delete one custom book and only data exclusively owned by that book."""
    bid = _book_id_int(db, book_id)
    book = db.query(Book).filter(Book.id == bid).first()
    if not book:
        return {"error": "Book not found"}
    if book.is_builtin:
        return {"error": "Cannot delete built-in books. You can deactivate them instead."}

    book_name = book.book_name
    word_ids = [
        row[0]
        for row in db.query(BookWord.word_id).filter(BookWord.book_id == bid).all()
    ]

    deleted_records = db.query(StudyRecord).filter(
        StudyRecord.book_id == bid
    ).delete(synchronize_session=False)
    deleted_links = db.query(BookWord).filter(
        BookWord.book_id == bid
    ).delete(synchronize_session=False)
    deleted_entries = db.query(DictionaryEntry).filter(
        DictionaryEntry.book_id == bid
    ).delete(synchronize_session=False)

    # A study word/review schedule is removed only when no other word book
    # references it. Shared words and their progress remain intact.
    deleted_words = 0
    if word_ids:
        remaining_word_ids = {
            row[0]
            for row in db.query(BookWord.word_id)
            .filter(BookWord.word_id.in_(word_ids))
            .all()
        }
        orphan_ids = [word_id for word_id in word_ids if word_id not in remaining_word_ids]
        if orphan_ids:
            deleted_records += db.query(StudyRecord).filter(
                StudyRecord.word_id.in_(orphan_ids)
            ).delete(synchronize_session=False)
            deleted_words = db.query(Word).filter(
                Word.id.in_(orphan_ids)
            ).delete(synchronize_session=False)

    db.delete(book)

    remaining_active = db.query(Book).filter(Book.is_active == True, Book.id != book_id).first()
    if not remaining_active:
        fallback = (
            db.query(Book)
            .filter(Book.id != book_id)
            .order_by(Book.is_builtin.desc(), Book.created_at.asc())
            .first()
        )
        if fallback:
            fallback.is_active = True

    db.commit()
    logger.info(
        "Deleted book '%s' (id=%s): entries=%s, words=%s, records=%s, links=%s",
        book_name,
        book_id,
        deleted_entries,
        deleted_words,
        deleted_records,
        deleted_links,
    )
    return {
        "success": True,
        "book_name": book_name,
        "deleted_entries": deleted_entries,
        "deleted_words": deleted_words,
        "deleted_study_records": deleted_records,
        "deleted_review_plans": deleted_words,
    }


@router.get("/api/books/{book_id}/progress")
def get_book_progress(book_id: str, db: Session = Depends(get_db)):
    """Get learning progress for a specific book from SQLite."""
    bid = _book_id_int(db, book_id)
    stats = _get_progress_stats_sql(db, bid)
    total = stats["total"]
    mastered = stats["mastered"]
    progress = round((mastered / total) * 100, 1) if total > 0 else 0.0

    book = db.query(Book).filter(Book.id == bid).first()
    return {
        "book_id": book_id,
        "book_name": book.book_name if book else book_id,
        "total_words": total,
        "studied_words": stats["studied"],
        "mastered_words": mastered,
        "review_due": stats["review_due"],
        "progress_percent": progress,
        "is_active": bool(book.is_active) if book else True,
        "created_at": book.created_at.isoformat() if (book and book.created_at) else "",
    }
