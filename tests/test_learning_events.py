"""Learning Event System tests.

Covers the rating/result mappings, JSON-safe serialization, and the end-to-end
recording of review / exercise / reading events into ``learning_events``.

Run:  python tests/test_learning_events.py
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

# Isolate the database before importing app (which runs init_db).
_tmp = tempfile.mkdtemp(prefix="wordmaster_test_events_")
os.environ["WORDMASTER_DATA_DIR"] = _tmp

from learning_events import (  # noqa: E402
    log_event, RESULT_TO_RATING, RATING_TO_RESULT, _json_safe, error_type_for,
)

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
print("  LEARNING EVENT SYSTEM TESTS")
print("=" * 60)

# ── 1. Rating/result mappings ──
print("\n=== 1. Rating/result mappings ===")
check("unknown -> again", RESULT_TO_RATING["unknown"] == "again")
check("fuzzy -> hard", RESULT_TO_RATING["fuzzy"] == "hard")
check("know -> good", RESULT_TO_RATING["know"] == "good")
check("too_easy -> easy", RESULT_TO_RATING["too_easy"] == "easy")
check("again -> incorrect", RATING_TO_RESULT["again"] == "incorrect")
check("good -> correct", RATING_TO_RESULT["good"] == "correct")

# ── 2. JSON-safe serialization (datetimes) ──
print("\n=== 2. JSON-safe serialization ===")
now = datetime.now()
safe = _json_safe({"due": now, "stability": 2.3, "nested": {"lapses": 1}})
check("datetime -> iso string", isinstance(safe["due"], str))
check("nested dict preserved", safe["nested"]["lapses"] == 1)
check("float preserved", safe["stability"] == 2.3)

# ── 3. error_type inference ──
print("\n=== 3. error_type inference ===")
check("correct -> none", error_type_for("know") == "none")
check("incorrect -> meaning (default)", error_type_for("unknown") == "meaning")

# ── 4. End-to-end: review + exercise + reading events ──
print("\n=== 4. End-to-end event recording ===")
from app import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from database import SessionLocal  # noqa: E402
from models import LearningEvent  # noqa: E402

client = TestClient(app)

q = client.get("/api/words/study-queue?count=2").json()
w = q[0]
client.post("/api/study", json={"word_id": w["english"], "result": "unknown", "response_time_ms": 1800, "session_id": "t-sess"})

client.post("/api/events", json={"word": w["english"], "activity_type": "confusion_test", "result": "incorrect", "user_answer": "economical", "correct_answer": "economic", "error_type": "confusion", "source_type": "exercise"})

client.post("/api/reading/add-word", json={"word": "lookupdemo", "meaning": "演示", "source_document": "Doc", "source_sentence": "sentence"})

db = SessionLocal()
events = db.query(LearningEvent).order_by(LearningEvent.id.asc()).all()
types = [e.activity_type for e in events]
check("review event recorded", "review" in types)
check("confusion_test event recorded", "confusion_test" in types)
check("reading_lookup event recorded", "reading_lookup" in types)

review_ev = next((e for e in events if e.activity_type == "review"), None)
check("review has rating again", review_ev is not None and review_ev.rating == "again")
check("review has fsrs_after", review_ev is not None and bool(review_ev.fsrs_after))
check("review has response_time", review_ev is not None and review_ev.response_time_ms == 1800)

ex_ev = next((e for e in events if e.activity_type == "confusion_test"), None)
check("exercise has error_type confusion", ex_ev is not None and ex_ev.error_type == "confusion")
check("exercise has user_answer", ex_ev is not None and ex_ev.user_answer == "economical")
db.close()

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
