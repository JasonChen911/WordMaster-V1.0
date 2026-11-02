"""Regression tests for the bug-fix batch: morphology search, material-import
hygiene (no preview pollution), reading-word lemma resolution, and repair.

Run:  python tests/test_bugfix_regression.py
"""

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

DATA_DIR = tempfile.mkdtemp(prefix="wordmaster_bugfix_")
os.environ["WORDMASTER_DATA_DIR"] = DATA_DIR

from app import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

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
print("  BUGFIX REGRESSION TEST")
print("=" * 60)
client = TestClient(app)

# ── Baseline word counts (to detect preview pollution) ──
from database import SessionLocal  # noqa: E402
from models import Word, DictionaryEntry, Book  # noqa: E402


def word_count():
    db = SessionLocal()
    n = db.query(Word).count()
    db.close()
    return n


def dict_count():
    db = SessionLocal()
    n = db.query(DictionaryEntry).count()
    db.close()
    return n


baseline_words = word_count()
baseline_dict = dict_count()

# ── A. Material ANALYZE must not write anything (preview ≠ import) ──
r = client.post("/api/material/analyze", json={
    "text": "Students study economics. Buses and boxes are everywhere. Students went to class.",
    "max_words": 6,
}).json()
cands = r.get("candidates", [])
check("A1 analyze returns candidates", len(cands) > 0, f"{len(cands)} candidates")
check("A2 analyze does NOT add study words", word_count() == baseline_words,
      f"{baseline_words} -> {word_count()}")
check("A3 analyze does NOT add dictionary rows", dict_count() == baseline_dict,
      f"{baseline_dict} -> {dict_count()}")

# ── B. Search resolves inflected forms to lemma ──
sw = client.get("/api/search/all", params={"q": "students"}).json()
study_words = [w["english"] for w in sw.get("study_words", [])]
check("B1 search 'students' returns 'student' (lemma)", "student" in study_words, str(study_words))

ds = client.get("/api/dictionary/search", params={"q": "students", "book_id": 0}).json()
# book_id 0 → no book filter; active book is used only when book_id is None. Use default.
ds = client.get("/api/dictionary/search", params={"q": "students"}).json()
dict_words = [d["word"] for d in ds.get("results", [])]
check("B2 dictionary search 'students' returns 'student'", "student" in dict_words, str(dict_words))

# ── C. Reading add-word lemmatizes an inflected form ──
before = word_count()
rd = client.post("/api/reading/add-word", json={
    "word": "Students", "meaning": "", "source_document": "AI Reading",
    "source_sentence": "Students study every day.",
}).json()
after = word_count()
check("C1 reading 'Students' resolves to existing 'student'", rd.get("english") == "student",
      str(rd.get("english")))
check("C2 no duplicate word row created", after == before, f"{before} -> {after}")

# ── D. Material IMPORT backfills meaning and folds to lemma ──
imp = client.post("/api/material/import", json={
    "book_name": "污染检测词书",
    "words": [
        {"word": "students", "meaning_zh": "", "example": ""},
        {"word": "study", "meaning_zh": "", "example": ""},
        {"word": "boxes", "meaning_zh": "", "example": ""},
    ],
}).json()
check("D1 import succeeded", imp.get("success") is True, str(imp))
check("D2 import does not create duplicate 'students' row",
      word_count() == before, f"{before} -> {word_count()}")

db = SessionLocal()
stud_row = db.query(Word).filter(Word.english == "student").first()
box_row = db.query(Word).filter(Word.english == "box").first()
study_row = db.query(Word).filter(Word.english == "study").first()
# "students"/"boxes" should NOT exist as their own rows (folded to lemma).
students_row = db.query(Word).filter(Word.english == "students").first()
boxes_row = db.query(Word).filter(Word.english == "boxes").first()
check("D3 'students' folded to 'student' (no separate row)", students_row is None)
check("D4 'boxes' folded to 'box' (no separate row)", boxes_row is None)
check("D5 student/box/study have Chinese meaning",
      bool(stud_row and stud_row.chinese) and bool(box_row and box_row.chinese) and bool(study_row and study_row.chinese))
db.close()

# ── E. Repair is idempotent and reports clean ──
from repair import repair_data  # noqa: E402
db = SessionLocal()
r1 = repair_data(db)
db.commit()
r2 = repair_data(db)
db.commit()
db.close()
check("E1 repair reports no empty-chinese words", r2["empty_chinese_words_remaining"] == 0, str(r2))
check("E2 repair reports no case-duplicates", r2["case_duplicate_words_remaining"] == 0, str(r2))

print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
