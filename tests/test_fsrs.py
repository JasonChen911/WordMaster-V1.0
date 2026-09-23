"""FSRS adaptive review engine tests.

Locks the WordMaster↔FSRS mapping so the four answer grades, mastery
threshold, proficiency mapping and explainability payload can't drift.

Run:  python tests/test_fsrs.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

from srs import (  # noqa: E402
    review_card,
    rating_from_result,
    explain_state,
    proficiency_from_state,
    is_mastered,
    RESULT_TO_RATING,
)
from fsrs import Rating, State  # noqa: E402

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
print("  FSRS ADAPTIVE REVIEW ENGINE TESTS")
print("=" * 60)

# ── 1. Answer grade → rating mapping ──
print("\n=== 1. Grade mapping ===")
check("unknown -> Again", rating_from_result("unknown") == Rating.Again)
check("fuzzy -> Hard", rating_from_result("fuzzy") == Rating.Hard)
check("know -> Good", rating_from_result("know") == Rating.Good)
check("too_easy -> Easy", rating_from_result("too_easy") == Rating.Easy)
check("unknown value falls back to Good", rating_from_result("???") == Rating.Good)

# ── 2. A new word schedules a future review ──
print("\n=== 2. New word review ===")
st = review_card(1, None, "know")
check("first review produces stability", st["stability"] is not None and st["stability"] > 0)
check("first review produces a future due", st["due"] > datetime.now())
check("reps incremented to 1", st["reps"] == 1)
check("no lapse on 'know'", st["lapses"] == 0)

# ── 3. Forgetting (unknown/again) causes a lapse + resets difficulty upward ──
print("\n=== 3. Lapse on 'unknown' ===")
st2 = review_card(1, st, "unknown")
check("lapse counted", st2["lapses"] == 1)
check("difficulty rises after a lapse", st2["difficulty"] > st["difficulty"])

# ── 4. Easy moves further out than Hard ──
print("\n=== 4. Easier grade → later due ===")
base = review_card(2, None, "know")
hard = review_card(3, None, "fuzzy")
easy = review_card(4, None, "too_easy")
check("too_easy due >= fuzzy due", easy["due"] >= hard["due"])

# ── 5. Explainability payload ──
print("\n=== 5. Explainability payload ===")
expl = explain_state(1, st)
check("has retrievability", "retrievability" in expl and 0.0 <= expl["retrievability"] <= 1.0)
check("has stability_days", "stability_days" in expl)
check("has forgetting_risk", expl["forgetting_risk"] in ("low", "medium", "high"))
check("has next_review", "next_review" in expl and expl["next_review"] is not None)

# ── 6. Proficiency mapping (0-5) ──
print("\n=== 6. Proficiency mapping ===")
check("new word -> 0", proficiency_from_state(None) == 0)
learning = {"state": 1, "stability": 1.0, "reps": 1, "difficulty": 5.0}
check("learning -> 1", proficiency_from_state(learning) == 1)
review_low = {"state": 2, "stability": 2.0, "reps": 3, "difficulty": 5.0}
check("review low stability -> 2", proficiency_from_state(review_low) == 2)
review_mid = {"state": 2, "stability": 5.0, "reps": 4, "difficulty": 4.0}
check("review mid stability -> 3", proficiency_from_state(review_mid) == 3)
review_high = {"state": 2, "stability": 10.0, "reps": 5, "difficulty": 4.0}
check("review high stability -> 4", proficiency_from_state(review_high) == 4)

# ── 7. Mastery threshold (Review state + >= 21 days stability) ──
print("\n=== 7. Mastery threshold ===")
not_mastered = {"state": 2, "stability": 10.0, "reps": 5, "difficulty": 4.0}
mastered = {"state": 2, "stability": 30.0, "reps": 6, "difficulty": 4.0}
check("short stability not mastered", is_mastered(not_mastered) is False)
check("long stability mastered", is_mastered(mastered) is True)
check("mastered -> proficiency 5", proficiency_from_state(mastered) == 5)

# ── 8. Stability grows across correct reviews (once in Review state) ──
print("\n=== 8. Stability growth across correct reviews ===")
state = None
prev_stability = 0.0
grew = False
for _ in range(12):
    state = review_card(99, state, "too_easy")
    if state["stability"] and state["stability"] > prev_stability + 0.01:
        grew = True
    prev_stability = state["stability"] or 0.0
check("stability increases over repeated easy reviews", grew)

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
