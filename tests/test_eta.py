"""Unified ETA tests — homepage and study page must agree.

Run:  python tests/test_eta.py
"""

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

_tmp = tempfile.mkdtemp(prefix="wordmaster_eta_")
os.environ["WORDMASTER_DATA_DIR"] = _tmp

from app import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from study_summary import compute_study_summary, format_estimated_time  # noqa: E402

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
print("  UNIFIED ETA TESTS")
print("=" * 60)
client = TestClient(app)

# ── 1. Home and study summary agree ──
print("\n=== 1. Home vs study summary agree ===")
home = client.get("/api/home").json()
study = client.get("/api/study/summary").json()
for k in ("daily_goal", "total_tasks", "new_tasks", "review_tasks", "remaining_tasks", "estimated_seconds", "display_text"):
    check(f"home.{k} == study.{k}", home.get(k) == study.get(k), f"{home.get(k)} vs {study.get(k)}")

# ── 2. Remaining decreases after studying ──
print("\n=== 2. Remaining decreases ===")
before = client.get("/api/study/summary").json()
q = client.get("/api/words/study-queue?count=20").json()
client.post("/api/study", json={"word_id": q[0]["english"], "result": "know", "response_time_ms": 4000})
after = client.get("/api/study/summary").json()
check("remaining decreased by 1", after["remaining_tasks"] == before["remaining_tasks"] - 1, f"{before['remaining_tasks']} -> {after['remaining_tasks']}")

# ── 3. Queue length matches total_tasks (no fill padding) ──
print("\n=== 3. Queue length matches total_tasks ===")
queue = client.get("/api/words/study-queue?count=20").json()
summary = client.get("/api/study/summary").json()
check("queue length == total_tasks", len(queue) == summary["total_tasks"], f"{len(queue)} vs {summary['total_tasks']}")

# ── 4. format_estimated_time rounding ──
print("\n=== 4. format_estimated_time rounding ===")
check("<60s -> 约 1 分钟", format_estimated_time(30) == "约 1 分钟")
check("60s -> 约 1 分钟", format_estimated_time(60) == "约 1 分钟")
check("61s -> 约 2 分钟 (round up)", format_estimated_time(61) == "约 2 分钟")
check("720s -> 约 12 分钟", format_estimated_time(720) == "约 12 分钟")
check("0s -> done", format_estimated_time(0) == "今天的任务已完成")

print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
