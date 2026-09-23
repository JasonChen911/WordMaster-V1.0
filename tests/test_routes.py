"""Route registration + import tests.

Verifies that the FastAPI route split kept every API endpoint intact:
- Each router module imports cleanly and exposes a router.
- All 48 API paths are present in the app's OpenAPI schema.
- A representative set of endpoints returns 200 (smoke test).

Run:  python tests/test_routes.py
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SERVER = ROOT / "server"
sys.path.insert(0, str(SERVER))
os.environ.setdefault("WORDMASTER_DATA_DIR", str(SERVER))

import logging  # noqa: E402
for n in ["app", "httpx", "sqlalchemy", "uvicorn", "asyncio", "db_init"]:
    logging.getLogger(n).setLevel(logging.ERROR)

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


# ── 1. Router module import test ──
print("=" * 60)
print("  ROUTER MODULE IMPORT TEST")
print("=" * 60)

ROUTER_MODULES = [
    "routers.words", "routers.stats", "routers.ai", "routers.books",
    "routers.dictionary", "routers.search", "routers.audio",
    "routers.games", "routers.media", "routers.material", "routers.insights",
    "routers.reading", "routers.teacher",
]

EXPECTED_ROUTE_COUNTS = {
    "words": 8,
    "stats": 5,
    "ai": 14,
    "books": 5,
    "dictionary": 9,
    "search": 3,
    "audio": 5,
    "games": 1,
    "media": 1,
    "material": 2,
    "insights": 4,
    "reading": 2,
    "teacher": 3,
}

import importlib  # noqa: E402

total_routes = 0
for modname in ROUTER_MODULES:
    try:
        mod = importlib.import_module(modname)
        router = getattr(mod, "router")
        n = len([r for r in router.routes if hasattr(r, "methods")])
        total_routes += n
        short = modname.split(".")[1]
        expected = EXPECTED_ROUTE_COUNTS.get(short)
        check(f"{modname} imports and exposes router ({n} routes)",
              expected is None or n == expected, f"expected {expected}, got {n}")
    except Exception as e:  # noqa: BLE001
        check(f"{modname} imports cleanly", False, f"{type(e).__name__}: {e}")

check("total router-declared routes == 62", total_routes == 62, f"got {total_routes}")

# ── 2. OpenAPI schema: all API paths present ──
print()
print("=" * 60)
print("  API PATH REGISTRATION TEST")
print("=" * 60)

from app import app  # noqa: E402

schema = app.openapi()
paths = set(schema.get("paths", {}).keys())

EXPECTED_PATHS = [
    "/api/dashboard",
    "/api/words/today",
    "/api/words/study-queue",
    "/api/words/all",
    "/api/words/{word_id}",
    "/api/words/{word_id}/fsrs",
    "/api/study",
    "/api/study/reset",
    "/api/words/{word_id}/favorite",
    "/api/games/words",
    "/api/stats",
    "/api/stats/weekly",
    "/api/stats/errors",
    "/api/debug/word-states",
    "/api/ai/explain",
    "/api/word/explain",
    "/api/ai/analyze-errors",
    "/api/ai/config-status",
    "/api/ai/save-key",
    "/api/ai/test-connection",
    "/api/ai/generate-reading",
    "/api/ai/chat",
    "/api/ai/status",
    "/api/ai/quiz",
    "/api/ai/report",
    "/api/ai/example",
    "/api/ai/word-analysis",
    "/api/ai/exercises",
    "/api/material/analyze",
    "/api/material/import",
    "/api/insights",
    "/api/confusion",
    "/api/confusion/{set_id}/toggle",
    "/api/ai/insights",
    "/api/reading/add-word",
    "/api/words/{word_id}/source",
    "/api/teacher/overview",
    "/api/teacher/courses",
    "/api/teacher/report",
    "/api/search",
    "/api/favorites",
    "/api/books",
    "/api/books/active",
    "/api/books/{book_id}/activate",
    "/api/books/{book_id}",
    "/api/books/{book_id}/progress",
    "/api/dictionary/search",
    "/api/dictionary/word/{word_text}",
    "/api/dictionary/import",
    "/api/dictionary/import/progress",
    "/api/dictionary/stats",
    "/api/dictionary/entries",
    "/api/dictionary/import/formats",
    "/api/dictionary/import/raw",
    "/api/dictionary/clear",
    "/api/search/all",
    "/api/audio/voices",
    "/api/audio/cache/stats",
    "/api/audio/cache",
    "/api/audio/{word}",
    "/api/audio/{word}/status",
    "/api/illustrations/{filename}",
]

missing = [p for p in EXPECTED_PATHS if p not in paths]
check("all 62 API paths present in schema", not missing, f"missing={missing}")
check("health present", "/health" in paths)

api_path_count = len([p for p in paths if p.startswith("/api/")])
print(f"    schema API paths: {api_path_count}")

# ── 3. Smoke test: representative GET endpoints return 200 ──
print()
print("=" * 60)
print("  API SMOKE TEST")
print("=" * 60)

from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(app)

GET_ENDPOINTS = [
    "/health",
    "/api/dashboard",
    "/api/words/today",
    "/api/words/study-queue?count=3",
    "/api/words/all",
    "/api/stats",
    "/api/stats/weekly",
    "/api/stats/errors",
    "/api/debug/word-states",
    "/api/ai/config-status",
    "/api/ai/status",
    "/api/search?q=abandon",
    "/api/favorites",
    "/api/books",
    "/api/books/active",
    "/api/dictionary/search?q=abandon&limit=3",
    "/api/dictionary/stats",
    "/api/dictionary/entries?per_page=10",
    "/api/dictionary/import/formats",
    "/api/search/all?q=test",
    "/api/audio/voices",
    "/api/audio/cache/stats",
]

for path in GET_ENDPOINTS:
    r = client.get(path)
    check(f"GET {path} -> 200", r.status_code == 200, f"status={r.status_code}")

# POST/DELETE methods are verified side-effect-free via the OpenAPI schema
# (executing them would mutate the dev DB / clear the audio cache).
METHOD_CHECKS = [
    ("post", "/api/study"),
    ("post", "/api/study/reset"),
    ("post", "/api/words/{word_id}/favorite"),
    ("post", "/api/ai/explain"),
    ("post", "/api/word/explain"),
    ("post", "/api/ai/analyze-errors"),
    ("post", "/api/ai/save-key"),
    ("post", "/api/ai/test-connection"),
    ("post", "/api/ai/generate-reading"),
    ("post", "/api/ai/chat"),
    ("post", "/api/ai/quiz"),
    ("post", "/api/ai/report"),
    ("post", "/api/books/{book_id}/activate"),
    ("delete", "/api/books/{book_id}"),
    ("post", "/api/dictionary/import"),
    ("get", "/api/dictionary/import/progress"),
    ("post", "/api/dictionary/import/raw"),
    ("delete", "/api/dictionary/clear"),
    ("delete", "/api/audio/cache"),
]

for method, path in METHOD_CHECKS:
    registered = method in schema.get("paths", {}).get(path, {})
    check(f"{method.upper()} {path} registered in schema", registered, f"path={path}")

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
