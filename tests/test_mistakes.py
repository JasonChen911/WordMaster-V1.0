"""Mistake book tests — daily/game sources, dedup, filter, persistence.

Run:  python tests/test_mistakes.py
"""

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

_tmp = tempfile.mkdtemp(prefix="wordmaster_mistakes_")
os.environ["WORDMASTER_DATA_DIR"] = _tmp

from app import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from database import SessionLocal  # noqa: E402
from models import MistakeRecord  # noqa: E402

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
print("  MISTAKE BOOK TESTS")
print("=" * 60)

client = TestClient(app)

# Get a couple of study words.
q = client.get("/api/words/study-queue?count=2").json()
w1, w2 = q[0], q[1]

# ── 1. Daily mistake (study wrong twice → count=2, one row) ──
print("\n=== 1. Daily mistake dedup ===")
client.post("/api/study", json={"word_id": w1["english"], "result": "unknown"})
client.post("/api/study", json={"word_id": w1["english"], "result": "unknown"})
db = SessionLocal()
daily = db.query(MistakeRecord).filter(MistakeRecord.word_id == w1["id"], MistakeRecord.source == "daily").all()
check("one daily row (dedup)", len(daily) == 1, f"{len(daily)} rows")
check("daily count == 2", daily[0].count == 2, daily[0].count)
db.close()

# ── 2. Game mistake via endpoint ──
print("\n=== 2. Game mistake write ===")
client.post("/api/mistakes", json={"word": w1["english"], "source": "game", "mistake_type": "spelling"})
client.post("/api/mistakes", json={"word": w1["english"], "source": "game", "mistake_type": "spelling"})
db = SessionLocal()
game = db.query(MistakeRecord).filter(MistakeRecord.word_id == w1["id"], MistakeRecord.source == "game").all()
check("one game row (dedup)", len(game) == 1, f"{len(game)} rows")
check("game count == 2", game[0].count == 2, game[0].count)
db.close()

# ── 3. Dual source preserved for the same word ──
print("\n=== 3. Dual source preserved ===")
db = SessionLocal()
rows = db.query(MistakeRecord).filter(MistakeRecord.word_id == w1["id"]).all()
sources = sorted(r.source for r in rows)
check("word has daily + game rows", sources == ["daily", "game"], sources)
db.close()

# ── 4. Filtering ──
print("\n=== 4. Filtering ===")
all_m = client.get("/api/mistakes").json()
daily_m = client.get("/api/mistakes?source=daily").json()
game_m = client.get("/api/mistakes?source=game").json()
check("all includes the word", any(m["word_id"] == w1["id"] for m in all_m["mistakes"]))
check("daily filter only daily", all(m["source"] == "daily" for m in daily_m["mistakes"]))
check("game filter only game", all(m["source"] == "game" for m in game_m["mistakes"]))

# ── 5. Stats ──
print("\n=== 5. Stats ===")
s = client.get("/api/mistakes/stats").json()
check("stats total >= 1", s["total"] >= 1, s)
check("stats daily >= 1", s["daily"] >= 1, s)
check("stats game >= 1", s["game"] >= 1, s)

# ── 6. Persistence across re-init ──
print("\n=== 6. Persistence across re-init ===")
from db_init import init_db  # noqa: E402
init_db()
db = SessionLocal()
still = db.query(MistakeRecord).filter(MistakeRecord.word_id == w1["id"]).count()
check("mistakes preserved after re-init", still == 2, still)
db.close()

# ── 7. Add to review + remove ──
print("\n=== 7. Add to review + remove ===")
r = client.post(f"/api/mistakes/{w1['id']}/review").json()
check("add to review succeeds", r.get("success") is True)
r2 = client.delete(f"/api/mistakes/{w1['id']}").json()
check("remove succeeds", r2.get("success") is True and r2.get("deleted") == 2)
db = SessionLocal()
left = db.query(MistakeRecord).filter(MistakeRecord.word_id == w1["id"]).count()
check("records gone after remove", left == 0, left)
db.close()

print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
