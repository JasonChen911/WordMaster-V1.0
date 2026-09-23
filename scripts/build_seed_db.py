"""Build a pre-initialized seed database for fast first launch.

WordMaster ships a clean, fully-initialized ``wordmaster.db`` so that a fresh
install copies it into AppData instead of re-parsing ~42k bundled word-list
rows on first boot (which can exceed the backend startup budget on slow or
antivirus-scanned machines).

The seed database contains ONLY built-in word books and an empty study history.
It is copied to AppData only when the user has no database yet (see
``database.py``); existing user data is never overwritten.

Usage (from the project root, using the project venv):

    .venv/Scripts/python.exe scripts/build_seed_db.py

Output: ``server/wordmaster_seed.db`` (bundled by ``wordmaster.spec``).
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SERVER = ROOT / "server"

# The project venv may not be on sys.path; add server/ explicitly.
sys.path.insert(0, str(SERVER))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="wordmaster_seed_"))
    # Force database.py to build a fresh DB in an isolated dir.
    os.environ["WORDMASTER_DATA_DIR"] = str(tmp)

    try:
        # Import after the env override so database.py resolves the temp dir.
        from db_init import init_db

        init_db()

        built = tmp / "wordmaster.db"
        if not built.exists():
            print(f"ERROR: init_db did not produce {built}")
            return 1

        target = SERVER / "wordmaster_seed.db"
        shutil.copy2(built, target)
        print(f"Seed database written: {target} ({target.stat().st_size} bytes)")
        return 0
    finally:
        # Remove the temp dir (ignore errors on Windows lock races).
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
