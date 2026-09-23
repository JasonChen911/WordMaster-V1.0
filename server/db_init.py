"""Database initialisation: schema creation, migrations, and built-in word books.

``init_db()`` is called once by ``app.py`` at startup.  It is kept separate from
the route modules so that importing a router never triggers database writes.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, text as sa_text
from sqlalchemy import func as sa_func

from database import engine, SessionLocal, Base, DATABASE_PATH
from models import (
    Word, StudyRecord, DailyStats, DictionaryEntry, Book, BookWord,
    WordAIExplanation, WordMemoryState, AIContentCache, ConfusionSet,
    SourceDocument, SourceWord, Course, Student, StudentWordStat,
    LearningEvent,
)
from seed import WORDS, BUILTIN_BOOKS
from confusion_seed import CONFUSION_SEED
from teacher_seed import (
    DEMO_CLASS_NAME, DEMO_COURSE, DEMO_STUDENTS, DEMO_STUDENT_STATS, DEMO_WEAK_WORDS,
)
from core import (
    _get_setting, _set_setting, _get_active_book_id, _book_id_str,
    _new_word, _fill_missing_word_fields, _link_book_words,
)

logger = logging.getLogger(__name__)

# Bump this whenever the bundled word-bank files change so existing installs
# re-run the built-in book initialisation once (then skip it on later launches).
_BUILTIN_BOOKS_VERSION = "2026.09.21"

_applied_versions: set = set()

# Keep at most this many automatic pre-migration backups.
_MAX_BACKUPS = 3


def _backup_database():
    """Snapshot the existing database before migrations touch it.

    Only runs when a real database exists and no backup was made today, so a
    user's study data is never overwritten by a migration without a safety copy.
    """
    try:
        db_path = Path(DATABASE_PATH)
        if not db_path.exists() or db_path.stat().st_size == 0:
            return
        today = datetime.now().strftime("%Y%m%d")
        backup = db_path.with_name(f"{db_path.stem}.bak-{today}{db_path.suffix}")
        if backup.exists():
            return
        shutil.copy2(db_path, backup)
        # Prune old backups beyond the cap.
        siblings = sorted(db_path.parent.glob(f"{db_path.stem}.bak-*{db_path.suffix}"))
        for stale in siblings[:-_MAX_BACKUPS]:
            try:
                stale.unlink()
            except OSError:
                pass
        logger.info("Pre-migration backup written: %s", backup.name)
    except Exception as exc:  # noqa: BLE001 — backup must never block startup
        logger.warning("Pre-migration backup skipped: %s", exc)


def init_db():
    _backup_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _migrate_existing(db)

        # Built-in word books are static in a release. After they have been
        # initialised once we skip the (expensive) full re-parse on every
        # launch, which keeps warm startup fast. The version marker is only
        # written after a successful initialisation.
        if _get_setting(db, "builtin_books_version") != _BUILTIN_BOOKS_VERSION:
            _initialize_builtin_books(db)
            _set_setting(db, "builtin_books_version", _BUILTIN_BOOKS_VERSION)
            db.commit()

        # Persist the active book into user_settings when missing, so the
        # string-ID setting stays consistent with Book.is_active after a fresh
        # install or an upgrade from an older release.
        if not _get_setting(db, "active_book"):
            active_bid = _get_active_book_id(db)
            active_str = _book_id_str(db, active_bid)
            if active_str:
                _set_setting(db, "active_book", active_str)
                db.commit()

        _log_startup_debug(db)
    finally:
        db.close()


def _seed_confusion_sets(db):
    """Insert the built-in confusion pairs once (never overwrites user state)."""
    try:
        existing = {
            (c.word_a, c.word_b)
            for c in db.query(ConfusionSet.word_a, ConfusionSet.word_b).all()
        }
        added = 0
        for item in CONFUSION_SEED:
            pair = (item["word_a"], item["word_b"])
            if pair not in existing:
                db.add(ConfusionSet(
                    word_a=item["word_a"],
                    word_b=item["word_b"],
                    distinction_cn=item["distinction_cn"],
                    memory_tip_cn=item["memory_tip_cn"],
                    example_en=item["example_en"],
                    example_cn=item["example_cn"],
                    source="builtin",
                ))
                existing.add(pair)
                added += 1
        if added:
            db.commit()
            logger.info("Seeded %s confusion sets", added)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning("Confusion set seeding skipped: %s", e)


def _seed_teacher_demo(db):
    """Seed the Local Classroom Demo (courses/students/word stats), idempotent.

    All seeded rows are flagged ``is_demo=True`` and are clearly labelled so the
    UI never presents them as real user data.
    """
    try:
        if not db.query(Course).filter(Course.is_demo == True).first():
            db.add(Course(
                name=DEMO_COURSE["name"],
                description=DEMO_COURSE["description"],
                is_demo=True,
            ))
            db.commit()
            logger.info("Seeded demo course")

        if not db.query(Student).filter(Student.is_demo == True).first():
            students = []
            for i, name in enumerate(DEMO_STUDENTS):
                studied, mastered, reviews, correct, lapses = DEMO_STUDENT_STATS[i]
                s = Student(
                    name=name, class_name=DEMO_CLASS_NAME, is_demo=True,
                    words_studied=studied, words_mastered=mastered,
                    total_reviews=reviews, correct_count=correct, lapses=lapses,
                )
                db.add(s)
                db.flush()
                students.append((s.id, name))
            db.commit()

            # Simulated weak-word stats for each demo student.
            for idx, (student_id, _name) in enumerate(students):
                words = DEMO_WEAK_WORDS[: (idx % 3) + 4]
                for word, wrong, acc, lapses in words:
                    db.add(StudentWordStat(
                        student_id=student_id,
                        word=word,
                        wrong_count=wrong + (idx % 2),
                        accuracy_rate=acc,
                        lapses=lapses,
                    ))
            db.commit()
            logger.info("Seeded %s demo students with simulated word stats", len(students))
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning("Teacher demo seeding skipped: %s", e)


def _log_startup_debug(db):
    """Print diagnostic information about word states on startup."""
    now = datetime.now()
    active = db.query(Book).filter(Book.is_active == True).first()

    logger.info("=" * 60)
    logger.info("  [DEBUG] WordMaster Startup -- Word State Debug")
    logger.info("=" * 60)

    if active:
        book_word_ids = [
            row[0]
            for row in db.query(BookWord.word_id)
            .filter(BookWord.book_id == active.id)
            .all()
        ]
        word_scope = Word.id.in_(book_word_ids) if book_word_ids else False
    else:
        word_scope = True

    base = db.query(Word)
    scoped = base.filter(word_scope) if word_scope is not True else base

    total = scoped.count()
    new_count = scoped.filter(Word.study_status == "new").count()
    learning_count = scoped.filter(Word.study_status == "learning").count()
    mastered_count = scoped.filter(Word.is_mastered == True).count()
    review_count_zero = scoped.filter(Word.review_count == 0).count()
    review_count_gt0 = scoped.filter(Word.review_count > 0).count()

    # Actual review-due: studied AND next_review <= now
    review_due = scoped.filter(
        Word.review_count > 0,
        Word.next_review <= now,
    ).count()

    logger.info(f"  Active Book: {active.book_name if active else '(none)'}  (id={active.id if active else 0})")
    logger.info(f"  Total Words: {total}")
    logger.info(f"  New (unstudied): {new_count}")
    logger.info(f"  Learning: {learning_count}")
    logger.info(f"  Mastered: {mastered_count}")
    logger.info(f"  Review Due: {review_due}")
    logger.info(f"  ---")
    logger.info(f"  review_count=0: {review_count_zero}")
    logger.info(f"  review_count>0: {review_count_gt0}")
    logger.info(f"  study_status='new': {new_count}")
    logger.info(f"  study_status='learning': {learning_count}")

    # Print first 5 review-due words and why
    review_words = scoped.filter(
        Word.review_count > 0,
        Word.next_review <= now,
    ).order_by(Word.next_review.asc()).limit(5).all()

    if review_words:
        logger.info("  --- Top 5 Review-Due Words ---")
        for i, w in enumerate(review_words, 1):
            logger.info(
                f"  {i}. {w.english} | "
                f"status={w.study_status} | "
                f"review_count={w.review_count} | "
                f"review_stage={w.review_stage} | "
                f"next_review={w.next_review.isoformat() if w.next_review else 'NULL'} | "
                f"last_review={w.last_reviewed_at.isoformat() if w.last_reviewed_at else 'NULL'} | "
                f"reason=review_count>0 AND next_review<=now"
            )
    else:
        logger.info("  --- Review queue is empty (correct) ---")

    # Also check: are there words with next_review in past but review_count=0?
    stale_new = scoped.filter(
        Word.review_count == 0,
        Word.next_review <= now,
    ).count()
    logger.info(f"  ---")
    logger.info(f"  [WARN] review_count=0 but next_review expired (NOT counted as review): {stale_new}")

    logger.info("=" * 60)


def _initialize_builtin_books(db):
    """Idempotently import bundled TXT files into words, dictionary and links."""
    existing_words = {
        word.english.lower(): word
        for word in db.query(Word).all()
    }

    # Keep the original fallback behavior if no TXT resources are present.
    if not BUILTIN_BOOKS and not existing_words:
        db.add_all([_new_word(entry) for entry in WORDS])
        db.commit()
        logger.warning("No bundled TXT word lists found; loaded fallback words")
        return

    books_by_filename = {
        (book.file_name or "").lower(): book
        for book in db.query(Book).all()
        if book.file_name
    }
    existing_links = {
        (book_id, word_id)
        for book_id, word_id in db.query(BookWord.book_id, BookWord.word_id).all()
    }
    initialized_books: list[Book] = []

    for filename, display_name, entries in BUILTIN_BOOKS:
        book = books_by_filename.get(filename)
        if not book:
            book = Book(
                book_name=display_name,
                file_name=filename,
                word_count=0,
                is_active=False,
                is_builtin=True,
            )
            db.add(book)
            db.flush()
            books_by_filename[filename] = book
        else:
            book.is_builtin = True
            # Always refresh book name from canonical display name
            book.book_name = display_name

        initialized_books.append(book)

        new_words = []
        for entry in entries:
            word = existing_words.get(entry[0])
            if word:
                _fill_missing_word_fields(word, entry)
            else:
                word = _new_word(entry)
                existing_words[entry[0]] = word
                new_words.append(word)
        if new_words:
            db.add_all(new_words)
            db.flush()

        missing_links = []
        for entry in entries:
            word = existing_words[entry[0]]
            key = (book.id, word.id)
            if key not in existing_links:
                existing_links.add(key)
                missing_links.append(BookWord(book_id=book.id, word_id=word.id))
        if missing_links:
            db.add_all(missing_links)

        actual_count = (
            db.query(DictionaryEntry)
            .filter(DictionaryEntry.book_id == book.id)
            .count()
        )
        if actual_count != len(entries):
            db.query(DictionaryEntry).filter(
                DictionaryEntry.book_id == book.id
            ).delete(synchronize_session=False)
            db.add_all([
                DictionaryEntry(
                    book_id=book.id,
                    word=entry[0],
                    phonetic=entry[1],
                    definition_cn=entry[2],
                    example=entry[3],
                    example_translation=entry[4],
                    source=filename,
                )
                for entry in entries
            ])
            actual_count = len(entries)
            logger.info(
                "Initialized built-in book %s: %s unique words",
                display_name,
                actual_count,
            )
        book.word_count = actual_count
        db.commit()

    # Backfill membership for word books imported by older releases.
    for book in db.query(Book).filter(Book.is_builtin == False).all():
        old_entries = (
            db.query(DictionaryEntry)
            .filter(DictionaryEntry.book_id == book.id)
            .all()
        )
        if old_entries:
            _link_book_words(
                db,
                book.id,
                [
                    (
                        entry.word.lower(),
                        entry.phonetic or "",
                        entry.definition_cn or entry.definition_en or "",
                        entry.example or "",
                        entry.example_translation or "",
                    )
                    for entry in old_entries
                ],
            )

    # Recalculate every book count from its real dictionary rows.
    counts = dict(
        db.query(DictionaryEntry.book_id, sa_func.count(DictionaryEntry.id))
        .group_by(DictionaryEntry.book_id)
        .all()
    )
    for book in db.query(Book).all():
        book.word_count = int(counts.get(book.id, 0))

    active = db.query(Book).filter(Book.is_active == True).first()
    if initialized_books and (not active or active.word_count == 0):
        db.query(Book).update({Book.is_active: False})
        initialized_books[0].is_active = True

    db.commit()
    logger.info(
        "Built-in word books ready: %s",
        ", ".join(f"{book.file_name}={book.word_count}" for book in initialized_books),
    )


def _ensure_migration_tracking(db) -> set:
    """Create migration tracking table and return set of applied migrations."""
    # Create schema_version table if not exists
    db.execute(sa_text("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()

    # Get list of already-applied migrations
    try:
        result = db.execute(sa_text("SELECT version FROM schema_version")).fetchall()
        return {row[0] for row in result}
    except Exception:
        return set()


def _apply_migration(db, version: str, sql: str):
    """Apply a single migration if not already applied."""
    if version not in _applied_versions:
        try:
            db.execute(sa_text(sql))
            db.execute(sa_text("INSERT INTO schema_version (version) VALUES (:v)"), {"v": version})
            db.commit()
            logger.info(f"Migration [{version}] applied successfully")
        except Exception as e:
            logger.warning(f"Migration [{version}] skipped: {e}")
            db.rollback()
    else:
        logger.debug(f"Migration [{version}] already applied, skipping")


def _migrate_existing(db):
    """Run all database migrations with version tracking."""
    global _applied_versions

    inspector = inspect(engine)

    # Initialize tracking
    _applied_versions = _ensure_migration_tracking(db)

    # ── Migration v1: words table new columns ──
    existing_words = {c["name"] for c in inspector.get_columns("words")}
    word_migrations = [
        ("v1.1_words_review_stage",     "ALTER TABLE words ADD COLUMN review_stage INTEGER DEFAULT 0"),
        ("v1.2_words_last_reviewed_at", "ALTER TABLE words ADD COLUMN last_reviewed_at DATETIME"),
        ("v1.3_words_accuracy_rate",    "ALTER TABLE words ADD COLUMN accuracy_rate FLOAT DEFAULT 0.0"),
        ("v1.4_words_proficiency",      "ALTER TABLE words ADD COLUMN proficiency INTEGER DEFAULT 0"),
    ]
    for ver, sql in word_migrations:
        col = ver.split("_", 2)[2]
        if col not in existing_words:
            _apply_migration(db, ver, sql)

    if "study_status" not in existing_words:
        _apply_migration(db, "v1.5_words_study_status",
                         "ALTER TABLE words ADD COLUMN study_status TEXT DEFAULT 'new'")

    if "illustration" not in existing_words:
        _apply_migration(db, "v1.6_words_illustration",
                         "ALTER TABLE words ADD COLUMN illustration TEXT DEFAULT ''")

    # Add illustration to dictionary table if missing
    existing_dict2 = {c["name"] for c in inspector.get_columns("dictionary")}
    if "illustration" not in existing_dict2:
        _apply_migration(db, "v6.9_dict_illustration",
                         "ALTER TABLE dictionary ADD COLUMN illustration TEXT DEFAULT ''")

    # Backfill study_status for any existing rows with NULL or inconsistent state
    try:
        # Fix NULL status → 'new'
        null_fixed = db.execute(sa_text(
            "UPDATE words SET study_status = 'new' WHERE study_status IS NULL OR study_status = ''"
        )).rowcount
        # Fix inconsistent: has review_count > 0 but still 'new'
        learning_fixed = db.execute(sa_text(
            "UPDATE words SET study_status = 'learning' WHERE review_count > 0 AND study_status = 'new'"
        )).rowcount
        if null_fixed or learning_fixed:
            db.commit()
            logger.info(
                f"Backfilled study_status: {null_fixed} NULL→new, {learning_fixed} new→learning"
            )
    except Exception as e:
        db.rollback()
        logger.warning(f"study_status backfill skipped: {e}")
    existing_ds = {c["name"] for c in inspector.get_columns("daily_stats")}
    ds_migrations = [
        ("v2.1_ds_correct_count", "ALTER TABLE daily_stats ADD COLUMN correct_count INTEGER DEFAULT 0"),
        ("v2.2_ds_total_reviews", "ALTER TABLE daily_stats ADD COLUMN total_reviews INTEGER DEFAULT 0"),
        ("v2.3_ds_minutes_studied", "ALTER TABLE daily_stats ADD COLUMN minutes_studied INTEGER DEFAULT 0"),
    ]
    for ver, sql in ds_migrations:
        col = ver.split("_", 2)[2]
        if col not in existing_ds:
            _apply_migration(db, ver, sql)

    # ── Migration v3: study_records new column ──
    existing_sr = {c["name"] for c in inspector.get_columns("study_records")}
    if "review_stage" not in existing_sr:
        _apply_migration(db, "v3.1_sr_review_stage",
                         "ALTER TABLE study_records ADD COLUMN review_stage INTEGER DEFAULT 0")
    if "book_id" not in existing_sr:
        _apply_migration(db, "v3.2_sr_book_id",
                         "ALTER TABLE study_records ADD COLUMN book_id INTEGER DEFAULT 0")
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_study_records_book_id ON study_records (book_id)"
        ))
        db.commit()

    # ── Migration v4: dictionary table ──
    tables = inspector.get_table_names()
    if "dictionary" not in tables:
        _apply_migration(db, "v4.1_create_dictionary",
                         "CREATE TABLE dictionary (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER DEFAULT 0, word TEXT NOT NULL, phonetic TEXT DEFAULT '', definition TEXT DEFAULT '', example TEXT DEFAULT '', audio TEXT DEFAULT '', source TEXT DEFAULT '', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        # Create index
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_dictionary_word ON dictionary (word)"))
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_dictionary_book_id ON dictionary (book_id)"))
        db.commit()

    # ── Migration v5: books table ──
    if "books" not in tables:
        _apply_migration(db, "v5.1_create_books",
                         "CREATE TABLE books (id INTEGER PRIMARY KEY AUTOINCREMENT, book_name TEXT NOT NULL, file_name TEXT DEFAULT '', word_count INTEGER DEFAULT 0, is_active BOOLEAN DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    existing_books = {c["name"] for c in inspector.get_columns("books")}
    if "is_builtin" not in existing_books:
        _apply_migration(db, "v5.2_books_is_builtin",
                         "ALTER TABLE books ADD COLUMN is_builtin BOOLEAN DEFAULT 0")

    # ── Migration v5.3: explicit book-to-word membership ──
    if "book_words" not in tables:
        _apply_migration(
            db,
            "v5.3_create_book_words",
            "CREATE TABLE book_words ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "book_id INTEGER NOT NULL, "
            "word_id INTEGER NOT NULL, "
            "CONSTRAINT uq_book_words_book_word UNIQUE (book_id, word_id), "
            "FOREIGN KEY(book_id) REFERENCES books (id), "
            "FOREIGN KEY(word_id) REFERENCES words (id))",
        )
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_book_words_book_id ON book_words (book_id)"
        ))
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_book_words_word_id ON book_words (word_id)"
        ))
        db.commit()

    # ── Migration v6: new professional dictionary columns ──
    existing_dict = {c["name"] for c in inspector.get_columns("dictionary")}
    dict_new_cols = {
        "definition_cn": "ALTER TABLE dictionary ADD COLUMN definition_cn TEXT DEFAULT ''",
        "definition_en": "ALTER TABLE dictionary ADD COLUMN definition_en TEXT DEFAULT ''",
        "part_of_speech": "ALTER TABLE dictionary ADD COLUMN part_of_speech TEXT DEFAULT ''",
        "example_translation": "ALTER TABLE dictionary ADD COLUMN example_translation TEXT DEFAULT ''",
        "audio_us": "ALTER TABLE dictionary ADD COLUMN audio_us TEXT DEFAULT ''",
        "audio_uk": "ALTER TABLE dictionary ADD COLUMN audio_uk TEXT DEFAULT ''",
        "synonyms": "ALTER TABLE dictionary ADD COLUMN synonyms TEXT DEFAULT ''",
        "antonyms": "ALTER TABLE dictionary ADD COLUMN antonyms TEXT DEFAULT ''",
    }
    migration_versions = [
        "v6.1_definition_cn", "v6.2_definition_en", "v6.3_part_of_speech",
        "v6.4_example_translation", "v6.5_audio_us", "v6.6_audio_uk",
        "v6.7_synonyms", "v6.8_antonyms",
    ]
    for ver, (col, sql) in zip(migration_versions, dict_new_cols.items()):
        if col not in existing_dict:
            _apply_migration(db, ver, sql)

    # Migrate old 'definition' → 'definition_cn', old 'audio' → 'audio_us'
    if "definition" in existing_dict and "definition_cn" in {c["name"] for c in inspector.get_columns("dictionary")}:
        try:
            cnt = db.execute(sa_text(
                "UPDATE dictionary SET definition_cn=definition WHERE definition_cn='' AND definition!=''"
            )).rowcount
            if cnt > 0:
                logger.info(f"Migrated {cnt} rows: definition → definition_cn")
                db.commit()
        except Exception:
            db.rollback()

    # ── v7.0: user_settings table (C-3 migration, Step 3) ──
    _apply_migration(db, "v7.0_user_settings",
        """CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

    # ── v8.0: word_ai_explanations cache table ──
    _apply_migration(db, "v8.0_word_ai_explanations",
        """CREATE TABLE IF NOT EXISTS word_ai_explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            explanation TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    # Ensure index on word column
    try:
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_word_ai_explanations_word ON word_ai_explanations (word)"
        ))
        db.commit()
    except Exception:
        db.rollback()

    # ── v9.0: word_memory_state (FSRS adaptive review state) ──
    _apply_migration(db, "v9.0_word_memory_state",
        """CREATE TABLE IF NOT EXISTS word_memory_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL UNIQUE,
            state INTEGER DEFAULT 1,
            step INTEGER DEFAULT 0,
            stability FLOAT,
            difficulty FLOAT,
            due DATETIME,
            last_review DATETIME,
            reps INTEGER DEFAULT 0,
            lapses INTEGER DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    try:
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_word_memory_state_word_id ON word_memory_state (word_id)"
        ))
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_word_memory_state_due ON word_memory_state (due)"
        ))
        db.commit()
    except Exception:
        db.rollback()

    # ── v10.0: ai_content_cache (level-aware AI content cache) ──
    _apply_migration(db, "v10.0_ai_content_cache",
        """CREATE TABLE IF NOT EXISTS ai_content_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            level TEXT DEFAULT 'CET4',
            exam_type TEXT DEFAULT 'general',
            content_type TEXT DEFAULT 'example',
            payload TEXT NOT NULL,
            model TEXT DEFAULT '',
            version TEXT DEFAULT '1',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_ai_content_cache_key UNIQUE (word, level, exam_type, content_type)
        )""")
    try:
        db.execute(sa_text(
            "CREATE INDEX IF NOT EXISTS ix_ai_content_cache_word ON ai_content_cache (word)"
        ))
        db.commit()
    except Exception:
        db.rollback()

    # ── v11.0: confusion_sets (易混词系统) ──
    _apply_migration(db, "v11.0_confusion_sets",
        """CREATE TABLE IF NOT EXISTS confusion_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_a TEXT NOT NULL,
            word_b TEXT NOT NULL,
            distinction_cn TEXT DEFAULT '',
            memory_tip_cn TEXT DEFAULT '',
            example_en TEXT DEFAULT '',
            example_cn TEXT DEFAULT '',
            mastered INTEGER DEFAULT 0,
            source TEXT DEFAULT 'builtin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_confusion_pair UNIQUE (word_a, word_b)
        )""")
    try:
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_confusion_word_a ON confusion_sets (word_a)"))
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_confusion_word_b ON confusion_sets (word_b)"))
        db.commit()
    except Exception:
        db.rollback()

    # Seed the built-in confusion pairs (idempotent).
    _seed_confusion_sets(db)

    # ── v13.0: teacher MVP tables (courses / students / student_word_stats) ──
    _apply_migration(db, "v13.0_courses",
        """CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            book_id INTEGER,
            is_demo INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    _apply_migration(db, "v13.1_students",
        """CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT DEFAULT 'Demo Class',
            is_demo INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    _apply_migration(db, "v13.2_student_word_stats",
        """CREATE TABLE IF NOT EXISTS student_word_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            wrong_count INTEGER DEFAULT 0,
            accuracy_rate FLOAT DEFAULT 0,
            lapses INTEGER DEFAULT 0,
            CONSTRAINT uq_student_word UNIQUE (student_id, word)
        )""")
    try:
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_student_word_stats_word ON student_word_stats (word)"))
        db.commit()
    except Exception:
        db.rollback()

    # Seed the clearly-labelled Local Classroom Demo data (idempotent).
    _seed_teacher_demo(db)

    # ── v14.0: learning_events (unified learning behavior record) ──
    _apply_migration(db, "v14.0_learning_events",
        """CREATE TABLE IF NOT EXISTS learning_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            book_id INTEGER DEFAULT 0,
            session_id TEXT DEFAULT '',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            activity_type TEXT NOT NULL,
            result TEXT DEFAULT '',
            rating TEXT DEFAULT '',
            response_time_ms INTEGER DEFAULT 0,
            user_answer TEXT DEFAULT '',
            correct_answer TEXT DEFAULT '',
            error_type TEXT DEFAULT '',
            source_type TEXT DEFAULT '',
            source_id INTEGER DEFAULT 0,
            fsrs_before TEXT DEFAULT '',
            fsrs_after TEXT DEFAULT '',
            client_version TEXT DEFAULT '',
            algorithm_version TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    try:
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_learning_events_word_id ON learning_events (word_id)"))
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_learning_events_activity ON learning_events (activity_type)"))
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_learning_events_timestamp ON learning_events (timestamp)"))
        db.commit()
    except Exception:
        db.rollback()

    # ── v12.0: source_documents + source_words (reading → vocab loop) ──
    _apply_migration(db, "v12.0_source_documents",
        """CREATE TABLE IF NOT EXISTS source_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    _apply_migration(db, "v12.1_source_words",
        """CREATE TABLE IF NOT EXISTS source_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            source_document_id INTEGER NOT NULL,
            source_sentence TEXT DEFAULT '',
            CONSTRAINT uq_source_word UNIQUE (word_id, source_document_id)
        )""")
    try:
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_source_words_word_id ON source_words (word_id)"))
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS ix_source_words_doc_id ON source_words (source_document_id)"))
        db.commit()
    except Exception:
        db.rollback()

    db.commit()
    logger.info("Database migration complete")
