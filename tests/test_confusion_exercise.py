"""Confusion engine + targeted exercise + insights aggregation tests.

Run:  python tests/test_confusion_exercise.py
"""

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

_tmp = tempfile.mkdtemp(prefix="wordmaster_conf_")
os.environ["WORDMASTER_DATA_DIR"] = _tmp

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
print("  CONFUSION + EXERCISE + INSIGHTS TESTS")
print("=" * 60)

client = TestClient(app)

# ── 1. Confusion sets seeded ──
print("\n=== 1. Confusion sets seeded ===")
r = client.get("/api/confusion").json()
sets = r.get("sets", [])
check("built-in confusion sets present", len(sets) >= 8, f"{len(sets)} sets")
check("economic/economical present", any(s["word_a"] == "economic" and s["word_b"] == "economical" for s in sets))
check("affect/effect present", any(s["word_a"] == "affect" and s["word_b"] == "effect" for s in sets))
check("each set has distinction", all(s.get("distinction_cn") for s in sets))

# ── 2. Exercise fallback (offline, valid structure) ──
print("\n=== 2. Exercise fallback validation ===")
from ai.services.exercise_service import fallback_questions  # noqa: E402

words = [{"english": "economic", "chinese": "经济的"}, {"english": "economical", "chinese": "节约的"}]
q = fallback_questions(words, "multiple_choice", 2)
check("fallback returns questions", len(q) == 2)
check("question has answer", bool(q[0].answer))
check("question has explanation", bool(q[0].explanation))
check("target word present", words[0]["english"] in q[0].target_words)

# Discrimination fallback
qd = fallback_questions(words, "discrimination", 1)
check("discrimination fallback works", len(qd) == 1)

# ── 3. Insights aggregation (event stats) ──
print("\n=== 3. Insights aggregation ===")
# Record a couple of study events to make stats non-trivial.
sq = client.get("/api/words/study-queue?count=3").json()
for w in sq[:2]:
    client.post("/api/study", json={"word_id": w["english"], "result": "unknown", "response_time_ms": 2000})
    client.post("/api/study", json={"word_id": w["english"], "result": "know", "response_time_ms": 1500})

ins = client.get("/api/insights").json()
events = ins.get("events", {})
check("events present", "total_events" in events)
check("total_events >= 4", events.get("total_events", 0) >= 4)
check("avg_response_time_ms > 0", events.get("avg_response_time_ms", 0) > 0)
check("error_breakdown has 'meaning'", "meaning" in events.get("error_breakdown", {}))

home = client.get("/api/home").json()
check("home has today_tasks", "today_tasks" in home)
check("home has estimated_minutes", "estimated_minutes" in home)
check("home streak is int", isinstance(home.get("streak_days"), int))

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
