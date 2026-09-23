"""Dictionary routes: search, word lookup, MDX/raw import, stats, entries, clear."""

import logging
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models import Book, DictionaryEntry
from core import _link_book_words

logger = logging.getLogger(__name__)

router = APIRouter()

# Global dict to track import progress
_import_progress: dict = {}


@router.get("/api/dictionary/search")
def search_dictionary(
    q: str = Query("", min_length=1),
    limit: int = Query(50, ge=1, le=200),
    book_id: int = Query(None, description="Filter by book, omit for active book"),
    db: Session = Depends(get_db),
):
    """Search dictionary with fuzzy matching, scoped to a book."""
    if not q.strip():
        return {"results": [], "total": 0}

    # Use active book if not specified
    if book_id is None:
        active = db.query(Book).filter(Book.is_active == True).first()
        book_id = active.id if active else 0

    query = db.query(DictionaryEntry).filter(
        DictionaryEntry.book_id == book_id,
        DictionaryEntry.word.ilike(f"{q.strip()}%"),
    )

    # For Chinese queries, search definition
    has_chinese = any("一" <= c <= "鿿" for c in q)
    if has_chinese:
        query = db.query(DictionaryEntry).filter(
            DictionaryEntry.book_id == book_id,
            DictionaryEntry.definition_cn.ilike(f"%{q.strip()}%"),
        )

    results = query.order_by(DictionaryEntry.word.asc()).limit(limit).all()
    return {
        "results": [
            {
                "id": r.id,
                "word": r.word,
                "phonetic": r.phonetic,
                "definition_cn": r.definition_cn or "",
                "definition_en": r.definition_en or "",
                "part_of_speech": r.part_of_speech or "",
                "example": r.example,
                "example_translation": r.example_translation or "",
                "audio_us": r.audio_us or "",
                "audio_uk": r.audio_uk or "",
                "synonyms": r.synonyms or "",
                "antonyms": r.antonyms or "",
                "source": r.source,
                "book_id": r.book_id,
            }
            for r in results
        ],
        "total": len(results),
        "book_id": book_id,
    }


@router.get("/api/dictionary/word/{word_text}")
def get_dictionary_word(
    word_text: str,
    book_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Look up a specific word in the dictionary."""
    if book_id is None:
        active = db.query(Book).filter(Book.is_active == True).first()
        book_id = active.id if active else 0

    entry = (
        db.query(DictionaryEntry)
        .filter(
            DictionaryEntry.word.ilike(word_text.strip()),
            DictionaryEntry.book_id == book_id,
        )
        .first()
    )
    if not entry:
        return {"found": False, "word": None}
    return {
        "found": True,
        "word": {
            "id": entry.id,
            "word": entry.word,
            "phonetic": entry.phonetic,
            "definition_cn": entry.definition_cn or "",
            "definition_en": entry.definition_en or "",
            "part_of_speech": entry.part_of_speech or "",
            "example": entry.example,
            "example_translation": entry.example_translation or "",
            "audio_us": entry.audio_us or "",
            "audio_uk": entry.audio_uk or "",
            "synonyms": entry.synonyms or "",
            "antonyms": entry.antonyms or "",
            "source": entry.source,
            "book_id": entry.book_id,
        },
    }


@router.post("/api/dictionary/import")
def import_dictionary(
    filepath: str = Query("", description="Absolute path to .mdx file"),
    book_name: str = Query("", description="Custom book name (uses filename if empty)"),
    db: Session = Depends(get_db),
):
    """Import an MDX dictionary into the database, creating a Book."""
    from mdx_reader import MDXReader

    global _import_progress

    if not filepath:
        return {"error": "Please provide filepath parameter"}

    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    if not path.suffix.lower() == ".mdx":
        return {"error": "Only .mdx files are supported"}

    # Determine book name
    name = book_name.strip() or path.stem

    # Create book record
    book = Book(book_name=name, file_name=path.name, word_count=0, is_active=False)
    db.add(book)
    db.commit()
    db.refresh(book)

    book_id = book.id
    _import_progress[book_id] = {"total": 0, "imported": 0, "status": "starting"}
    logger.info(f"Starting MDX import: {filepath} → book_id={book_id} name='{name}'")

    def do_import():
        session = SessionLocal()
        try:
            from mdx_reader import parse_mdx_entry

            with MDXReader(path) as reader:
                batch = []
                batch_size = 200
                total = 0
                imported = 0
                study_entries = []

                for entry in reader.entries():
                    total += 1
                    try:
                        parsed = parse_mdx_entry(entry["definition"])
                        # parse_mdx_entry returns: phonetic_us, phonetic_uk,
                        # definition_cn, definition_en, examples (list of {en,cn})
                        phonetic = parsed.get("phonetic_us") or parsed.get("phonetic_uk") or ""
                        examples = parsed.get("examples") or []
                        example_text = "\n".join(
                            f"{ex.get('en', '')}  {ex.get('cn', '')}".strip()
                            for ex in examples
                            if isinstance(ex, dict)
                        ) or ""
                        dict_entry = DictionaryEntry(
                            book_id=book_id,
                            word=entry["word"].strip(),
                            phonetic=phonetic,
                            definition_cn=parsed.get("definition_cn") or "",
                            definition_en=parsed.get("definition_en") or "",
                            example=example_text,
                            source=path.name,
                        )
                        batch.append(dict_entry)
                        study_entries.append((
                            entry["word"].strip().lower(),
                            phonetic,
                            parsed.get("definition_cn") or "",
                            example_text,
                            "",
                        ))
                        imported += 1

                        if len(batch) >= batch_size:
                            session.add_all(batch)
                            session.commit()
                            batch = []
                            _import_progress[book_id] = {"total": total, "imported": imported, "status": "importing"}
                    except Exception:
                        continue

                if batch:
                    session.add_all(batch)
                    session.commit()

                # Update book word count
                book = session.query(Book).filter(Book.id == book_id).first()
                if book:
                    book.word_count = imported
                    _link_book_words(session, book_id, study_entries)
                    session.commit()

                _import_progress[book_id] = {"total": total, "imported": imported, "status": "done"}
                logger.info(f"MDX import complete: book_id={book_id} imported={imported} total={total}")
        except Exception as e:
            _import_progress[book_id] = {"status": "error", "error": str(e)}
            logger.error(f"MDX import error: {e}")
        finally:
            session.close()

    threading.Thread(target=do_import, daemon=True, name="WordMaster-MDX-Import").start()

    return {
        "success": True,
        "message": "Import started",
        "book_id": book_id,
        "book_name": name,
    }


@router.get("/api/dictionary/import/progress")
def get_import_progress(book_id: int = Query(0)):
    """Get the progress of an ongoing MDX import."""
    global _import_progress
    if book_id in _import_progress:
        return _import_progress[book_id]
    return {"status": "unknown"}


@router.get("/api/dictionary/stats")
def get_dictionary_stats(db: Session = Depends(get_db)):
    """Get dictionary stats grouped by book."""
    books = db.query(Book).all()
    sources_list = []
    total_entries = 0
    for b in books:
        count = db.query(DictionaryEntry).filter(DictionaryEntry.book_id == b.id).count()
        total_entries += count
        if count > 0:
            sources_list.append({"name": b.book_name, "count": count, "book_id": b.id, "is_active": b.is_active})
    return {"total_entries": total_entries, "sources": sources_list}


@router.get("/api/dictionary/entries")
def list_dictionary_entries(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=10, le=200),
    book_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Paginated dictionary entries."""
    if book_id is None:
        active = db.query(Book).filter(Book.is_active == True).first()
        book_id = active.id if active else 0

    query = db.query(DictionaryEntry).filter(DictionaryEntry.book_id == book_id)
    total = query.count()
    entries = (
        query.order_by(DictionaryEntry.word.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "entries": [
            {
                "id": e.id,
                "word": e.word,
                "phonetic": e.phonetic,
                "definition": (e.definition_cn or e.definition_en or "")[:200],
                "source": e.source,
            }
            for e in entries
        ],
        "total": total, "page": page, "per_page": per_page,
    }


@router.get("/api/dictionary/import/formats")
def get_import_formats():
    """Get supported import formats and templates."""
    return {
        "formats": {
            "txt": {
                "description": "Tab-separated text file",
                "template": "word\tphonetic\tchinese\texample_en\texample_cn\nabandon\t/əˈbændən/\t放弃\tHe abandoned his plan.\t他放弃了计划。",
            },
            "csv": {
                "description": "CSV file",
                "template": "word,phonetic,chinese,example_en,example_cn\nabandon,/əˈbændən/,放弃,He abandoned his plan.,他放弃了计划。",
            },
            "json": {
                "description": "JSON array",
                "template": '[{"word":"abandon","phonetic":"/əˈbændən/","chinese":"放弃","example_en":"He abandoned his plan.","example_cn":"他放弃了计划。"}]',
            },
        }
    }


@router.post("/api/dictionary/import/raw")
async def import_raw_data(
    request: Request,
    book_name: str = Query("New Book"),
    file_format: str = Query("txt"),
):
    """Import words from raw text content sent as request body.

    The body is read in the async endpoint, then the (potentially large)
    parsing + database work runs in a worker thread so the event loop stays
    responsive and the UI never blocks during a big import.
    """
    from starlette.concurrency import run_in_threadpool

    try:
        body = (await request.body()).decode("utf-8")
    except Exception as e:
        return {"error": f"Failed to read request body: {e}"}

    if not body.strip():
        return {"error": "Empty content"}

    return await run_in_threadpool(
        _import_raw_sync, body, book_name.strip(), file_format.strip()
    )


def _import_raw_sync(body: str, book_name: str, file_format: str) -> dict:
    """Synchronous worker for raw word-list import (runs in a threadpool)."""
    import json as json_module
    import csv as csv_module
    import io

    from seed import parse_wordlist_line

    db = SessionLocal()
    try:
        words_to_add = []
        skipped = 0

        try:
            if file_format == "json":
                data = json_module.loads(body)
                if isinstance(data, dict):
                    data = data.get("words", data.get("data", []))
                if not isinstance(data, list):
                    return {"error": "JSON must be an array of word objects"}
                for item in data:
                    if isinstance(item, dict) and "word" in item:
                        words_to_add.append((
                            str(item.get("word", "")).strip().lower(),
                            item.get("phonetic", ""),
                            item.get("chinese", item.get("meaning", item.get("definition", ""))),
                            item.get("example_en", item.get("example", "")),
                            item.get("example_cn", item.get("translation", "")),
                        ))
                    elif isinstance(item, str):
                        words_to_add.append((item.strip().lower(), "", "", "", ""))

            elif file_format == "csv":
                reader = csv_module.reader(io.StringIO(body))
                for row in reader:
                    if not row or not row[0].strip():
                        continue
                    word = row[0].strip().lower()
                    if word in {"word", "english", "单词"}:
                        continue
                    phonetic = row[1].strip() if len(row) > 1 else ""
                    chinese = row[2].strip() if len(row) > 2 else ""
                    example_en = row[3].strip() if len(row) > 3 else ""
                    example_cn = row[4].strip() if len(row) > 4 else ""
                    words_to_add.append((word, phonetic, chinese, example_en, example_cn))

            else:  # txt — tab-separated
                for line in body.splitlines():
                    parsed = parse_wordlist_line(line)
                    if parsed and parsed[0] not in {"word", "english"}:
                        words_to_add.append(parsed)
                    elif line.strip():
                        skipped += 1
        except Exception as e:
            return {"error": f"Parse error: {e}"}

        if not words_to_add:
            return {"error": "No valid words found in content"}

        # Keep one row per word in a word book.
        unique_words = {}
        for entry in words_to_add:
            unique_words.setdefault(entry[0].lower(), entry)
        skipped += len(words_to_add) - len(unique_words)
        words_to_add = list(unique_words.values())

        # Create book
        name = book_name or "Imported"
        book = Book(book_name=name, file_name=f"import.{file_format}", word_count=0, is_active=False)
        db.add(book)
        db.commit()
        db.refresh(book)

        # Insert words
        imported = 0
        for word_tup in words_to_add:
            try:
                entry = DictionaryEntry(
                    book_id=book.id,
                    word=word_tup[0],
                    phonetic=word_tup[1],
                    definition_cn=word_tup[2],
                    example=word_tup[3],
                    example_translation=word_tup[4],
                    source=name,
                )
                db.add(entry)
                imported += 1
                if imported % 500 == 0:
                    db.commit()
            except Exception:
                skipped += 1
                continue

        # Update book word count
        book.word_count = imported
        _link_book_words(db, book.id, words_to_add)
        db.commit()

        logger.info(f"Imported {imported} words into book '{name}' (id={book.id}), skipped {skipped}")

        return {
            "success": True,
            "book_id": book.id,
            "book_name": name,
            "imported": imported,
            "skipped": skipped,
        }
    finally:
        db.close()


@router.delete("/api/dictionary/clear")
def clear_dictionary(
    book_id: int = Query(0, description="Book ID to clear"),
    db: Session = Depends(get_db),
):
    """Clear dictionary entries for a specific book."""
    if book_id <= 0:
        return {"error": "Please specify book_id"}
    count = db.query(DictionaryEntry).filter(DictionaryEntry.book_id == book_id).delete()
    # Update book word count
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.word_count = 0
    db.commit()
    logger.info(f"Cleared {count} dictionary entries for book_id={book_id}")
    return {"success": True, "deleted": count}
