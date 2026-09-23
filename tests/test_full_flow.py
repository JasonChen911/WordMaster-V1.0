"""End-to-end core-loop verification (manual-flow checklist, automated).

Simulates the full WordMaster core loop (A→V from the acceptance criteria):
material → AI analyze → confirm → study → FSRS → repeated errors → diagnosis →
targeted practice → learning event → insights → reading loop → teacher preview.

Run:  python tests/test_full_flow.py
"""

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

DATA_DIR = tempfile.mkdtemp(prefix="wordmaster_flow_")
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
print("  FULL CORE-LOOP FLOW TEST")
print("=" * 60)
client = TestClient(app)

# B/C — import + AI analyze material
TEXT = ("Artificial intelligence is transforming education. Students must "
        "distinguish between economic growth and economical solutions, and "
        "evaluate their approach to learning.")
r = client.post("/api/material/analyze", json={"text": TEXT, "max_words": 8}).json()
cands = r.get("candidates", [])
check("B/C material analyzed with candidates", len(cands) > 0, f"{len(cands)} candidates")

# E — add 5 words
chosen = cands[:5]
words = [{"word": c["word"], "meaning_zh": c.get("meaning_zh", ""), "example": c.get("example", "")} for c in chosen]
imp = client.post("/api/material/import", json={"book_name": "流程测试词书", "words": words}).json()
check("E imported words", imp.get("imported", 0) >= 1)

# F/G — study with all four ratings
q = client.get("/api/words/study-queue?count=20").json()
ratings = ["unknown", "fuzzy", "know", "too_easy"]
results = []
for i, w in enumerate(q[:4]):
    rr = client.post("/api/study", json={"word_id": w["english"], "result": ratings[i % 4], "response_time_ms": 1500 + i * 500}).json()
    results.append(rr.get("fsrs"))
check("F/G study recorded with FSRS", all(r and "retrievability" in r for r in results))

# H — FSRS data changed
fs = client.get(f"/api/words/{q[0]['id']}/fsrs").json()
check("H FSRS state changed (has_history)", fs.get("has_history") is True)

# I/J/K — restart persistence
from database import SessionLocal  # noqa: E402
from models import WordMemoryState  # noqa: E402
db = SessionLocal()
mem_count = db.query(WordMemoryState).count()
db.close()
import importlib  # noqa: E402
from db_init import init_db  # noqa: E402
init_db()  # simulate restart
db2 = SessionLocal()
mem_count2 = db2.query(WordMemoryState).count()
db2.close()
check("K FSRS state preserved across restart", mem_count == mem_count2, f"{mem_count} vs {mem_count2}")

# L — simulate repeated errors on one word
target = q[0]["english"]
for _ in range(3):
    client.post("/api/study", json={"word_id": target, "result": "unknown", "response_time_ms": 2500})

# M — AI diagnosis (may be ai_available=False if no key; structure must be valid)
d = client.post("/api/ai/word-analysis", json={"word": target, "summary": {}}).json()
check("M diagnosis returns valid structure", "diagnosis" in d or "ai_available" in d)

# N/O/P — targeted practice + event recording
ex = client.post("/api/ai/exercises", json={"words": [{"english": "economic", "chinese": "经济的"}, {"english": "economical", "chinese": "节约的"}], "exercise_type": "discrimination", "count": 2}).json()
check("N practice generated", len(ex.get("questions", [])) >= 1 or ex.get("ai_available") is False)
ev = client.post("/api/events", json={"word": "economic", "activity_type": "confusion_test", "result": "incorrect", "user_answer": "economical", "correct_answer": "economic", "error_type": "confusion", "source_type": "exercise"}).json()
check("P practice recorded as event", ev.get("success") is True)

# Q/R — insights stats
ins = client.get("/api/insights").json()
check("Q insights events present", ins.get("events", {}).get("total_events", 0) > 0)

# S/T/U — reading loop + source sentence
rd = client.post("/api/reading/add-word", json={"word": "flowword", "meaning": "流程", "source_document": "AI and Education", "source_sentence": "AI is transforming education."}).json()
src = client.get(f"/api/words/{rd['word_id']}/source").json()
check("U source sentence recorded", src.get("found") is True and "transforming" in src.get("source_sentence", ""))

# V — teacher preview
t = client.get("/api/teacher/overview").json()
check("V teacher preview has demo data", t.get("is_demo") is True and t.get("class_stats", {}).get("student_count", 0) > 0)

print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
