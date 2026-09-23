"""Project-facts consistency test.

Locks the canonical numbers that PROJECT_FACTS.md reports, so the stats script
and the real code cannot silently drift. Run:

    python tests/test_project_stats.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "server"))

from scripts.project_stats import (  # noqa: E402
    collect_routes, collect_tables, collect_pages,
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
print("  PROJECT FACTS CONSISTENCY TEST")
print("=" * 60)

api_total, health, static, per_module = collect_routes()
check("47 /api/* routes", api_total == 47, f"got {api_total}")
check("1 /health route", health == 1, f"got {health}")
check("2 static/SPA fallbacks", static == 2, f"got {static}")
check("9 router modules", len(per_module) == 9, f"got {len(per_module)}")

business_tables, core_tables = collect_tables()
if business_tables is not None:
    check("8 business tables", len(core_tables) == 8, f"got {len(core_tables)}")
    check("9 tables incl schema_version", len(business_tables) == 9,
          f"got {len(business_tables)}")
    check("sqlite_sequence excluded", "sqlite_sequence" not in business_tables)

page_files, primary_routes, all_routes = collect_pages()
check("10 primary pages", len(primary_routes) == 10, f"got {len(primary_routes)}")
check("13 page components", len(page_files) == 13, f"got {len(page_files)}")
check("13 frontend routes", len(all_routes) == 13, f"got {len(all_routes)}")

# Review schedule: 7 stages, no 90-day stage.
core_text = (ROOT / "server" / "core.py").read_text(encoding="utf-8", errors="ignore")
check("core.py is the single source of truth",
      "EBBINGHAUS_INTERVALS" in core_text and "get_next_review_interval" in core_text)
check("no 90-day stage in core.py", "90 * 24" not in core_text)

print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)
