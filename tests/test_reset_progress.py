"""Regression test for the word-book "reset progress" flow.

Verifies the full data chain behind a per-book reset:
  book A fully learned → reset → progress zeroed → queue re-populated →
  persists across a simulated restart → book B's exclusive data untouched.

Run:  python tests/test_reset_progress.py
"""

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

DATA_DIR = tempfile.mkdtemp(prefix="wordmaster_reset_")
os.environ["WORDMASTER_DATA_DIR"] = DATA_DIR

from app import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from database import SessionLocal  # noqa: E402
from models import Word, Book, BookWord, WordMemoryState, StudyRecord  # noqa: E402
from core import _book_id_int  # noqa: E402

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
print("  RESET PROGRESS REGRESSION TEST")
print("=" * 60)
client = TestClient(app)

# ── Locate two books: A (reset target) and B (must stay untouched) ──
books = client.get("/api/books").json()["books"]
assert len(books) >= 2, "need at least two books"
bookA = books[0]
bookB = books[1]

# Activate book A
client.post(f"/api/books/{bookA['id']}/activate")

db = SessionLocal()
aid = _book_id_int(db, bookA["id"])
bid = _book_id_int(db, bookB["id"])
wa = [r[0] for r in db.query(BookWord.word_id).filter(BookWord.book_id == aid).all()]
wb = [r[0] for r in db.query(BookWord.word_id).filter(BookWord.book_id == bid).all()]
wa_set = set(wa)
wb_exclusive = [w for w in wb if w not in wa_set]
check("A1 book A has words", len(wa) > 0, f"{len(wa)} words")
check("A2 book B has exclusive words", len(wb_exclusive) > 0, f"{len(wb_exclusive)} words")

# ── Simulate "book A fully learned": every word mastered ──
db.query(Word).filter(Word.id.in_(wa)).update(
    {"study_status": "mastered", "is_mastered": True, "review_count": 5},
    synchronize_session=False)
# Give book B three exclusive words an in-progress (learning) state to detect 误伤
b_markers = wb_exclusive[:3]
db.query(Word).filter(Word.id.in_(b_markers)).update(
    {"study_status": "learning", "is_mastered": False, "review_count": 2},
    synchronize_session=False)
db.commit()

# ── Queue must be empty when fully learned ──
q_before = client.get(f"/api/words/study-queue?book_id={bookA['id']}&count=20").json()
check("B1 fully-learned book has empty queue", len(q_before) == 0, f"{len(q_before)} words")

# ── Reset book A ──
r = client.post(f"/api/study/reset?book_id={bookA['id']}").json()
check("C1 reset returns success", r.get("success") is True, str(r))

# ── Queue re-populated after reset ──
q_after = client.get(f"/api/words/study-queue?book_id={bookA['id']}&count=20").json()
check("C2 queue re-populated after reset", len(q_after) > 0, f"{len(q_after)} words")

# ── Progress zeroed ──
new_count = db.query(Word).filter(Word.id.in_(wa), Word.study_status == "new").count()
check("C3 book A words reset to 'new'", new_count == len(wa), f"{new_count}/{len(wa)}")
mem_count = db.query(WordMemoryState).filter(WordMemoryState.word_id.in_(wa)).count()
check("C4 book A memory state cleared", mem_count == 0, f"{mem_count} rows")

# ── Book B untouched ──
learn_b = db.query(Word).filter(Word.id.in_(b_markers), Word.study_status == "learning").count()
check("D1 book B exclusive words untouched", learn_b == len(b_markers), f"{learn_b}/{len(b_markers)}")
rec_b = db.query(StudyRecord).filter(StudyRecord.book_id == bid).count()
check("D2 book B study records untouched", rec_b == 0, f"{rec_b} rows")

# ── Persistence across a simulated restart ──
from db_init import init_db  # noqa: E402
init_db()
db2 = SessionLocal()
new_count2 = db2.query(Word).filter(Word.id.in_(wa), Word.study_status == "new").count()
check("E1 reset persists after restart", new_count2 == len(wa), f"{new_count2}/{len(wa)}")
learn_b2 = db2.query(Word).filter(Word.id.in_(b_markers), Word.study_status == "learning").count()
check("E2 book B still untouched after restart", learn_b2 == len(b_markers), f"{learn_b2}/{len(b_markers)}")
db2.close()

db.close()
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
