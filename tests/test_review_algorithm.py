"""Review-algorithm single-source-of-truth tests.

Locks the Ebbinghaus schedule to the real implementation so that docs and the
code can never silently drift apart again.

The authoritative definition lives in ``server/core.py``:
    EBBINGHAUS_INTERVALS = {0: 4h, 1: 1d, 2: 2d, 3: 4d, 4: 7d, 5: 15d, 6: 30d}

Run:  python tests/test_review_algorithm.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

from core import EBBINGHAUS_INTERVALS, get_next_review_interval  # noqa: E402

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
print("  REVIEW ALGORITHM (single source of truth) TESTS")
print("=" * 60)

# ── 1. The canonical schedule: 7 stages, 4h → 1d → 2d → 4d → 7d → 15d → 30d ──
print("\n=== 1. EBBINGHAUS_INTERVALS ===")
expected = {0: 4, 1: 24, 2: 48, 3: 96, 4: 168, 5: 360, 6: 720}
check("schedule has exactly 7 stages (0..6)", EBBINGHAUS_INTERVALS == expected,
      str(EBBINGHAUS_INTERVALS))

for stage, hours in expected.items():
    check(f"stage {stage} -> {hours}h", EBBINGHAUS_INTERVALS.get(stage) == hours)

# ── 2. First study / correct answer advances one stage ──
print("\n=== 2. Correct answer (know / too_easy) advances one stage ===")
# stage 0 + know -> stage 1 -> 24h (1 day)
ns, iv = get_next_review_interval(0, "know")
check("stage0 + know -> stage 1", ns == 1, f"stage={ns}")
check("stage0 + know -> 24h (1 day)", iv == 24, f"{iv}h")

ns, iv = get_next_review_interval(0, "too_easy")
check("stage0 + too_easy -> stage 1", ns == 1, f"stage={ns}")
check("stage0 + too_easy -> 24h", iv == 24, f"{iv}h")

# ── 3. Full progression 0 → 6 through consecutive correct answers ──
print("\n=== 3. Full correct-answer progression reaches final stage ===")
progression = []
stage = 0
for _ in range(7):
    stage, iv = get_next_review_interval(stage, "know")
    progression.append((stage, iv))

check("7 correct answers reach stage 6", stage == 6, f"final stage={stage}")
check("progression caps at stage 6", [s for s, _ in progression][-1] == 6)
# intervals seen after each correct answer: 24, 48, 96, 168, 360, 720
seen_intervals = [iv for _, iv in progression]
check("interval sequence 24→48→96→168→360→720 (last repeats)",
      seen_intervals == [24, 48, 96, 168, 360, 720, 720],
      str(seen_intervals))

# ── 4. Final stage stays capped ──
print("\n=== 4. Final stage (6) does not overflow ===")
ns, iv = get_next_review_interval(6, "know")
check("stage6 + know stays 6", ns == 6, f"stage={ns}")
check("stage6 + know -> 720h (30 days)", iv == 720, f"{iv}h")

# ── 5. fuzzy keeps stage (repeat same interval) ──
print("\n=== 5. fuzzy keeps the same stage ===")
for s in (0, 1, 3, 6):
    ns, iv = get_next_review_interval(s, "fuzzy")
    check(f"stage{s} + fuzzy stays {s}", ns == s, f"stage={ns}")
    check(f"stage{s} + fuzzy -> {expected[s]}h", iv == expected[s], f"{iv}h")

# ── 6. unknown resets to stage 0 (4 hours) ──
print("\n=== 6. unknown resets to stage 0 (4 hours) ===")
for s in (0, 2, 5, 6):
    ns, iv = get_next_review_interval(s, "unknown")
    check(f"stage{s} + unknown -> stage 0", ns == 0, f"stage={ns}")
    check(f"stage{s} + unknown -> 4h", iv == 4, f"{iv}h")

# ── 7. The intervals are the canonical 4h/1d/2d/4d/7d/15d/30d ──
print("\n=== 7. Canonical human-readable sequence ===")
check("no 90-day stage exists", 90 * 24 not in EBBINGHAUS_INTERVALS.values(),
      str(EBBINGHAUS_INTERVALS.values()))
check("first stage is 4 hours (not skipped)", EBBINGHAUS_INTERVALS[0] == 4)
check("last stage is 30 days (720h)", EBBINGHAUS_INTERVALS[6] == 720)

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
