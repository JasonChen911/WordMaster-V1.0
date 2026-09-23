"""Regression tests for the two confirmed production bugs.

A. Games dynamic chunk exists and is HTTP-accessible (200, text/javascript)
B. Backend startup readiness detection (/health polling)
C. Backend early-exit surfaces the real error (not a generic timeout)
D. Fresh database first launch (isolated data dir)
E. Existing database upgrade (idempotent migration, data preserved)
F. Port-in-use is reported clearly (not "failed within 6 seconds")

Run:  python tests/test_startup_regression.py
"""
import os
import sys
import socket
import subprocess
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SERVER = ROOT / "server"
sys.path.insert(0, str(SERVER))
sys.path.insert(0, str(ROOT))

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


def _games_chunk_name():
    assets = ROOT / "web" / "dist" / "assets"
    for p in sorted(assets.glob("Games-*.js")):
        return p.name
    return None


# ═══════════════════════════════════════════════════════════════════
print("=" * 60)
print("  STARTUP / ASSETS REGRESSION")
print("=" * 60)

# ── A. Games chunk + /health via TestClient ──
print("\n=== A. Games 动态 chunk 存在并可 HTTP 访问 ===")
import logging
for n in ["app", "httpx", "sqlalchemy", "uvicorn", "asyncio"]:
    logging.getLogger(n).setLevel(logging.ERROR)

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

gname = _games_chunk_name()
check("Games chunk file exists in dist", gname is not None, str(gname))
if gname:
    r = client.get(f"/assets/{gname}")
    check("GET /assets/Games-*.js -> 200", r.status_code == 200, f"status={r.status_code}")
    ct = r.headers.get("content-type", "")
    check("Content-Type is text/javascript", "javascript" in ct, ct)
    check("Body is not HTML (not a 404/SPA fallback)", not r.text.lstrip().startswith("<"), "served HTML!")

r = client.get("/health")
check("GET /health -> 200 ok", r.status_code == 200 and r.json().get("status") == "ok", str(r.text[:80]))

# ── B. Backend ready detection (real server, isolated temp DB) ──
print("\n=== B. 后端启动 ready 检测 ===")
b_code = (
    "import sys, os\n"
    "sys.path.insert(0, os.environ['ROOT'])\n"
    "sys.path.insert(0, os.environ['SERVER'])\n"
    "import logging\n"
    "for n in ['app','httpx','sqlalchemy','uvicorn','asyncio']:\n"
    "    logging.getLogger(n).setLevel(logging.ERROR)\n"
    "import main\n"
    "port = main.find_free_port(8100, 8120)\n"
    "thread = main.start_backend(port)\n"
    "print('READY', port)\n"
)
b_env = os.environ.copy()
b_env["ROOT"] = str(ROOT)
b_env["SERVER"] = str(SERVER)
b_env["WORDMASTER_DATA_DIR"] = tempfile.mkdtemp(prefix="wm_b_")
b = subprocess.run([sys.executable, "-c", b_code], env=b_env, capture_output=True, text=True, timeout=180)
check("start_backend reports READY (backend became ready)", "READY" in b.stdout, b.stdout[-400:] + b.stderr[-400:])

# ── C. Backend early-exit surfaces real error ──
print("\n=== C. 后端提前退出时能获取真正错误 ===")
import main

# Fake a fast `app` so we don't run the real init_db in this in-process test.
if "app" not in sys.modules:
    sys.modules["app"] = types.ModuleType("app")
sys.modules["app"].app = object()

import uvicorn

def _boom(*a, **k):
    raise RuntimeError("synthetic bind failure")

_orig_run = uvicorn.run
uvicorn.run = _boom
try:
    try:
        main.start_backend(main.find_free_port(8121, 8129))
        check("start_backend raised on backend crash", False, "no exception raised")
    except RuntimeError as e:
        ok = "exited during startup" in str(e) and "synthetic bind failure" in str(e)
        check("raised with real cause (not generic timeout)", ok, str(e))
finally:
    uvicorn.run = _orig_run

# ── F. Port-in-use reported clearly ──
print("\n=== F. 端口占用处理 ===")
def _addr_in_use(*a, **k):
    raise OSError("[Errno 10048] address already in use")

uvicorn.run = _addr_in_use
try:
    try:
        main.start_backend(main.find_free_port(8121, 8129))
        check("start_backend raised on port conflict", False, "no exception raised")
    except RuntimeError as e:
        check("message mentions port in use", "in use" in str(e) or "占用" in str(e), str(e))
finally:
    uvicorn.run = _orig_run
    del sys.modules["app"]

# ── D. Fresh database first launch (isolated) ──
print("\n=== D. 全新用户首次启动（隔离目录）===")
tmpd = tempfile.mkdtemp(prefix="wm_fresh_")
d_code = (
    "import sys, os, sqlite3\n"
    "sys.path.insert(0, os.environ['SERVER'])\n"
    "import logging\n"
    "for n in ['app','httpx','sqlalchemy','uvicorn','asyncio']:\n"
    "    logging.getLogger(n).setLevel(logging.ERROR)\n"
    "from database import DATABASE_PATH\n"
    "from app import app  # triggers init_db (fresh DB)\n"
    "db = sqlite3.connect(str(DATABASE_PATH))\n"
    "tables = {r[0] for r in db.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}\n"
    "need = ['words','dictionary','books','book_words','study_records','daily_stats','user_settings','word_ai_explanations','schema_version']\n"
    "missing = [t for t in need if t not in tables]\n"
    "wc = db.execute('SELECT COUNT(*) FROM words').fetchone()[0]\n"
    "books = db.execute('SELECT COUNT(*) FROM books').fetchone()[0]\n"
    "print('MISSING', missing, 'WORDS', wc, 'BOOKS', books)\n"
)
d_env = os.environ.copy()
d_env["SERVER"] = str(SERVER)
d_env["WORDMASTER_DATA_DIR"] = tmpd
d = subprocess.run([sys.executable, "-c", d_code], env=d_env, capture_output=True, text=True, timeout=180)
check("fresh DB: all tables created", "MISSING []" in d.stdout, d.stdout[-400:] + d.stderr[-400:])
check("fresh DB: built-in words loaded", "WORDS" in d.stdout and "WORDS 0" not in d.stdout, d.stdout[-400:])
check("fresh DB: books created", "BOOKS" in d.stdout and "BOOKS 0" not in d.stdout, d.stdout[-400:])

# ── E. Existing database upgrade (idempotent) ──
print("\n=== E. 老用户数据库升级（幂等）===")
e_code = (
    "import sys, os, sqlite3\n"
    "sys.path.insert(0, os.environ['SERVER'])\n"
    "import logging\n"
    "for n in ['app','httpx','sqlalchemy','uvicorn','asyncio']:\n"
    "    logging.getLogger(n).setLevel(logging.ERROR)\n"
    "from database import DATABASE_PATH\n"
    "from app import app  # re-runs migrations on existing DB\n"
    "db = sqlite3.connect(str(DATABASE_PATH))\n"
    "wc = db.execute('SELECT COUNT(*) FROM words').fetchone()[0]\n"
    "active = db.execute(\"SELECT value FROM user_settings WHERE key='active_book'\").fetchone()\n"
    "print('WORDS', wc, 'ACTIVE', active is not None)\n"
)
e_env = os.environ.copy()
e_env["SERVER"] = str(SERVER)
e = subprocess.run([sys.executable, "-c", e_code], env=e_env, capture_output=True, text=True, timeout=180)
check("existing DB: migration idempotent (no error)", e.returncode == 0, e.stderr[-400:])
check("existing DB: data preserved", "WORDS" in e.stdout and "ACTIVE True" in e.stdout, e.stdout[-400:])

# ═══════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
