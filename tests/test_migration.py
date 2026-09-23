"""Database migration safety tests.

Verifies that a fresh database creates all tables and that re-running init_db
on an existing database is idempotent and preserves existing study data.

Run:  python tests/test_migration.py
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} | {detail}")


print("=" * 60)
print("  DATABASE MIGRATION TESTS")
print("=" * 60)

# ── 1. Fresh DB creates all tables ──
print("\n=== 1. Fresh DB creates all expected tables ===")
_tmp = tempfile.mkdtemp(prefix="wordmaster_mig_")
os.environ["WORDMASTER_DATA_DIR"] = _tmp

from db_init import init_db  # noqa: E402
from database import engine  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

init_db()
insp = inspect(engine)
tables = set(insp.get_table_names())

EXPECTED = {
    "words", "book_words", "books", "dictionary", "word_memory_state",
    "study_records", "daily_stats", "word_ai_explanations", "ai_content_cache",
    "confusion_sets", "source_documents", "source_words", "courses",
    "students", "student_word_stats", "learning_events", "schema_version",
    "user_settings",
}
missing = EXPECTED - tables
check("all expected tables present", not missing, f"missing={missing}")
check("learning_events table exists", "learning_events" in tables)
check("word_memory_state table exists", "word_memory_state" in tables)

# ── 2. Re-running init_db is idempotent ──
print("\n=== 2. init_db is idempotent ===")
from database import SessionLocal  # noqa: E402
from models import Word, StudyRecord  # noqa: E402

db = SessionLocal()
# Insert a marker study record to verify it survives a second init_db.
w = db.query(Word).first()
db.add(StudyRecord(word_id=w.id, book_id=0, result="know", review_stage=0))
db.commit()
marker_id = db.query(StudyRecord).order_by(StudyRecord.id.desc()).first().id
db.close()

init_db()  # re-run

db2 = SessionLocal()
still_there = db2.query(StudyRecord).filter(StudyRecord.id == marker_id).first()
check("existing study record preserved after re-init", still_there is not None)
db2.close()

# ── 3. schema_version migration tracking is populated ──
print("\n=== 3. schema_version tracking ===")
db3 = SessionLocal()
from sqlalchemy import text
versions = [r[0] for r in db3.execute(text("SELECT version FROM schema_version")).fetchall()]
check("migrations recorded", len(versions) > 0, f"{len(versions)} versions")
check("learning_events migration recorded", "v14.0_learning_events" in versions)
db3.close()

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
