"""Shared domain logic for WordMaster.

This module is the single source of truth for:
- The Ebbinghaus review schedule (``EBBINGHAUS_INTERVALS`` /
  ``get_next_review_interval``).  Do NOT duplicate these numbers anywhere else.
- Book ID mapping (JSON string ID <-> SQLite integer id).
- Word serialization and study-queue / progress query helpers.
- User-settings read/write helpers.

Routers import from here instead of from ``app``, which keeps the route modules
free of circular imports.
"""

from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, text as sa_text

from models import Word, Book, BookWord, DailyStats, SourceWord, SourceDocument


# ─── Ebbinghaus intervals (in hours) ────────────────────────────
# DEPRECATED: review scheduling is now handled by the FSRS engine
# (``server/srs/engine.py``). These values are retained only for the legacy
# ``test_review_algorithm`` contract and are no longer used by the study path.
EBBINGHAUS_INTERVALS = {
    0: 4,       # First review: 4 hours
    1: 24,      # 1 day
    2: 48,      # 2 days
    3: 96,      # 4 days
    4: 168,     # 7 days
    5: 360,     # 15 days
    6: 720,     # 30 days
}


def get_next_review_interval(stage: int, result: str) -> tuple[int, int]:
    """Calculate next Ebbinghaus review stage and interval.

    Args:
        stage: Current review stage (0-6)
        result: 'too_easy', 'know', 'fuzzy', or 'unknown'

    Returns:
        (new_stage, interval_hours)
    """
    if result in ("too_easy", "know"):
        new_stage = min(6, stage + 1)
    elif result == "fuzzy":
        new_stage = max(0, stage)  # Stay at same stage
    else:  # "unknown"
        new_stage = 0  # Reset to beginning

    interval = EBBINGHAUS_INTERVALS.get(new_stage, 720)
    return new_stage, interval


# ─── Book ID mapping (JSON string ID ↔ SQLite book_name) ──────

BOOK_ID_MAP = {
    "四级词汇": "CET4",
    "六级词汇": "CET6",
    "托福词汇": "TOEFL",
    "考研词汇": "考研",
    "高中词汇": "高中",
}
BOOK_NAME_BY_ID = {v: k for k, v in BOOK_ID_MAP.items()}


def _get_active_book_id(db: Session) -> int:
    """Get the active book's SQLite integer ID from user_settings."""
    row = db.execute(sa_text("SELECT value FROM user_settings WHERE key = 'active_book'")).fetchone()
    book_name_cn = BOOK_NAME_BY_ID.get(row[0]) if row else None
    if book_name_cn:
        book = db.query(Book).filter(Book.book_name == book_name_cn).first()
        if book:
            return book.id
    book = db.query(Book).filter(Book.is_active == True).first()
    if book:
        return book.id
    book = db.query(Book).first()
    return book.id if book else 0


def _get_book_scoped_word_ids(db: Session, book_id: int = None):
    """Return set of word_ids belonging to the given (or active) book."""
    if book_id is None:
        book_id = _get_active_book_id(db)
    return {
        row[0]
        for row in db.query(BookWord.word_id).filter(BookWord.book_id == book_id).all()
    }


def _book_id_str(db: Session, book_id_int: int = None) -> str:
    """Convert a SQLite book ID to the JSON-compatible string ID."""
    if book_id_int is None:
        book_id_int = _get_active_book_id(db)
    book = db.query(Book).filter(Book.id == book_id_int).first()
    if book:
        return BOOK_ID_MAP.get(book.book_name, book.book_name)
    return ""


def _book_id_int(db: Session, book_id_str: str) -> int:
    """Convert a JSON-compatible string book ID to SQLite integer ID."""
    book_name_cn = BOOK_NAME_BY_ID.get(book_id_str, book_id_str)
    book = db.query(Book).filter(Book.book_name == book_name_cn).first()
    return book.id if book else 0


def _word_to_dict(word: Word) -> dict:
    """Serialize a Word ORM object to the JSON-compatible dict."""
    return {
        "id": word.id,
        "english": word.english,
        "phonetic": word.phonetic or "",
        "chinese": word.chinese or "",
        "example_en": word.example_en or "",
        "example_cn": word.example_cn or "",
        "memory_tip": "",
        "ai_source": "static",
        "context": "",
        "study_status": word.study_status or "new",
        "review_count": word.review_count or 0,
        "review_stage": word.review_stage or 0,
        "difficulty": word.difficulty or 2.5,
        "is_favorite": bool(word.is_favorite),
        "is_mastered": bool(word.is_mastered),
        "accuracy_rate": word.accuracy_rate or 0.0,
        "proficiency": word.proficiency or 0,
        "next_review": word.next_review.isoformat() if word.next_review else None,
        "last_reviewed_at": word.last_reviewed_at.isoformat() if word.last_reviewed_at else None,
        "source_document": "",
        "source_sentence": "",
    }


def _generate_study_queue_sql(db: Session, book_id_int: int, count: int = 20) -> list[dict]:
    """Generate a study queue from SQLite with Ebbinghaus priority.

    Priority:
      1. Review-due words (Ebbinghaus order, never shuffled)
      2. New words (random order, stable per day via date-based seed)
      3. Fill with remaining words (random, same seed)
    """
    import random as _random

    # Cheap existence check — avoids materialising the whole book's ID set.
    if not db.query(BookWord.id).filter(BookWord.book_id == book_id_int).first():
        return []

    now = datetime.now()
    # Seed by date + book_id → same order all day, different each day
    rng = _random.Random(date.today().toordinal() * 1000 + book_id_int)

    queue: list[Word] = []
    used_ids: set[int] = set()

    # Priority 1: Review-due (learning + next_review expired) — NEVER shuffled
    review = (
        db.query(Word)
        .join(BookWord, BookWord.word_id == Word.id)
        .filter(BookWord.book_id == book_id_int,
                Word.study_status == "learning", Word.next_review <= now)
        .order_by(Word.next_review.asc())
        .limit(count)
        .all()
    )
    queue.extend(review)
    used_ids.update(w.id for w in review)

    # Fetch only IDs first (lightweight), shuffle in Python, then load just the
    # words actually needed — avoids materialising every new/remaining word as a
    # full ORM object on large books.
    def _pick_ids(filter_args):
        ids = [
            row[0]
            for row in db.query(Word.id)
            .join(BookWord, BookWord.word_id == Word.id)
            .filter(BookWord.book_id == book_id_int, *filter_args)
            .order_by(Word.id.asc())
            .all()
        ]
        rng.shuffle(ids)
        return ids

    # Priority 2: New words (never studied) — shuffled, stable per day
    if len(queue) < count:
        needed = count - len(queue)
        picked = _pick_ids([
            Word.id.notin_(used_ids),
            Word.study_status == "new", Word.review_count == 0,
        ])[:needed]
        if picked:
            by_id = {w.id: w for w in db.query(Word).filter(Word.id.in_(picked)).all()}
            queue.extend(by_id[i] for i in picked)
            used_ids.update(picked)

    # Priority 3: Fill with remaining words — shuffled, same seed
    if len(queue) < count:
        needed = count - len(queue)
        picked = _pick_ids([Word.id.notin_(used_ids)])[:needed]
        if picked:
            by_id = {w.id: w for w in db.query(Word).filter(Word.id.in_(picked)).all()}
            queue.extend(by_id[i] for i in picked)

    result = [_word_to_dict(w) for w in queue]
    _attach_sources(db, result)
    return result


def _attach_sources(db: Session, word_dicts: list[dict]):
    """Attach first-seen source context to each word dict (batch query)."""
    ids = [w["id"] for w in word_dicts if w.get("id")]
    if not ids:
        return
    rows = (
        db.query(SourceWord.word_id, SourceDocument.title, SourceWord.source_sentence)
        .join(SourceDocument, SourceDocument.id == SourceWord.source_document_id)
        .filter(SourceWord.word_id.in_(ids))
        .all()
    )
    by_word: dict[int, tuple] = {}
    for word_id, title, sentence in rows:
        if word_id not in by_word:  # first source wins
            by_word[word_id] = (title, sentence)
    for w in word_dicts:
        src = by_word.get(w["id"])
        if src:
            w["source_document"] = src[0]
            w["source_sentence"] = src[1]


def _get_progress_stats_sql(db: Session, book_id_int: int) -> dict:
    """Calculate per-book progress stats with a single SQL aggregate.

    Previously this loaded every Word object in the book into memory and
    iterated it in Python. On large word books (10k–50k+ words) that runs on
    the dashboard's periodic refresh, so it is now computed in SQL via the
    ``book_words`` membership table.
    """
    total = (
        db.query(sa_func.count(BookWord.id))
        .filter(BookWord.book_id == book_id_int)
        .scalar()
    ) or 0

    if total == 0:
        return {"total": 0, "new": 0, "learning": 0, "mastered": 0,
                "studied": 0, "review_due": 0, "today_minutes": 0, "proficiency": {}}

    now = datetime.now()

    # A word belongs to exactly one of mastered / learning / new. COALESCE on
    # is_mastered mirrors the previous Python check (NULL treated as not-mastered).
    row = db.execute(
        sa_text(
            "SELECT "
            "  COALESCE(SUM(CASE WHEN (COALESCE(is_mastered,0) = 1 OR study_status = 'mastered') THEN 1 ELSE 0 END), 0) AS mastered, "
            "  COALESCE(SUM(CASE WHEN NOT (COALESCE(is_mastered,0) = 1 OR study_status = 'mastered') AND COALESCE(review_count,0) > 0 THEN 1 ELSE 0 END), 0) AS learning, "
            "  COALESCE(SUM(CASE WHEN NOT (COALESCE(is_mastered,0) = 1 OR study_status = 'mastered') AND COALESCE(review_count,0) = 0 THEN 1 ELSE 0 END), 0) AS new, "
            "  COALESCE(SUM(CASE WHEN COALESCE(review_count,0) > 0 THEN 1 ELSE 0 END), 0) AS studied, "
            "  COALESCE(SUM(CASE WHEN COALESCE(review_count,0) > 0 AND next_review IS NOT NULL AND next_review <= :now THEN 1 ELSE 0 END), 0) AS review_due "
            "FROM words w JOIN book_words bw ON bw.word_id = w.id "
            "WHERE bw.book_id = :bid"
        ),
        {"now": now, "bid": book_id_int},
    ).fetchone()

    prof_rows = db.execute(
        sa_text(
            "SELECT COALESCE(proficiency, 0) AS p, COUNT(*) AS c "
            "FROM words w JOIN book_words bw ON bw.word_id = w.id "
            "WHERE bw.book_id = :bid GROUP BY p"
        ),
        {"bid": book_id_int},
    ).fetchall()
    prof_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for p, c in prof_rows:
        level = int(p or 0)
        prof_dist[level] = prof_dist.get(level, 0) + int(c)

    # Today's study minutes
    today_str = now.date().isoformat()
    daily = db.query(DailyStats).filter(DailyStats.date == today_str).first()
    today_minutes = daily.minutes_studied if daily else 0

    return {
        "total": total,
        "new": int(row[2]),
        "learning": int(row[1]),
        "mastered": int(row[0]),
        "studied": int(row[3]),
        "review_due": int(row[4]),
        "today_minutes": today_minutes,
        "proficiency": prof_dist,
    }


def _get_setting(db: Session, key: str) -> str:
    """Read a value from user_settings, or '' when missing."""
    row = db.execute(
        sa_text("SELECT value FROM user_settings WHERE key = :k"), {"k": key}
    ).fetchone()
    return row[0] if row else ""


def _set_setting(db: Session, key: str, value: str):
    db.execute(
        sa_text(
            "INSERT OR REPLACE INTO user_settings (key, value, updated_at) "
            "VALUES (:k, :v, datetime('now'))"
        ),
        {"k": key, "v": value},
    )


def _new_word(entry: tuple[str, str, str, str, str]) -> Word:
    return Word(
        english=entry[0],
        phonetic=entry[1],
        chinese=entry[2],
        example_en=entry[3],
        example_cn=entry[4],
    )


def _fill_missing_word_fields(word: Word, entry: tuple[str, str, str, str, str]):
    """Enrich an existing study word without overwriting learning progress."""
    if not word.phonetic and entry[1]:
        word.phonetic = entry[1]
    if not word.chinese and entry[2]:
        word.chinese = entry[2]
    if not word.example_en and entry[3]:
        word.example_en = entry[3]
    if not word.example_cn and entry[4]:
        word.example_cn = entry[4]


def _link_book_words(
    db: Session,
    book_id: int,
    entries: list[tuple[str, str, str, str, str]],
) -> int:
    """Upsert study words and create membership links for one word book."""
    if not entries:
        return 0

    existing_words = {
        word.english.lower(): word
        for word in db.query(Word).all()
    }
    unique_entries = {}
    for entry in entries:
        unique_entries.setdefault(entry[0].lower(), entry)

    new_words = []
    for word_text, entry in unique_entries.items():
        word = existing_words.get(word_text)
        if word:
            _fill_missing_word_fields(word, entry)
        else:
            word = _new_word(entry)
            existing_words[word_text] = word
            new_words.append(word)
    if new_words:
        db.add_all(new_words)
        db.flush()

    linked_ids = {
        row[0]
        for row in db.query(BookWord.word_id).filter(BookWord.book_id == book_id).all()
    }
    new_links = [
        BookWord(book_id=book_id, word_id=existing_words[word_text].id)
        for word_text in unique_entries
        if existing_words[word_text].id not in linked_ids
    ]
    if new_links:
        db.add_all(new_links)
    return len(new_links)
