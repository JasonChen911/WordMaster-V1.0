"""Consistent SQLite backups while the live database uses WAL mode."""
import sqlite3
from contextlib import closing
from pathlib import Path


def create_sqlite_backup(source: Path, destination: Path) -> None:
    destination = Path(destination)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(f"file:{Path(source).resolve().as_posix()}?mode=ro", uri=True)) as live:
            with closing(sqlite3.connect(temporary)) as snapshot:
                live.backup(snapshot)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def needs_upgrade_backup(source: Path, schema_version: str, books_version: str) -> bool:
    """Only snapshot when startup may migrate schema or rebuild built-in books."""
    try:
        with closing(sqlite3.connect(f"file:{Path(source).resolve().as_posix()}?mode=ro", uri=True)) as db:
            migrated = db.execute("SELECT 1 FROM schema_version WHERE version=?", (schema_version,)).fetchone()
            books = db.execute("SELECT value FROM user_settings WHERE key='builtin_books_version'").fetchone()
            if not migrated or not books or books[0] != books_version:
                return True
            duplicates = db.execute(
                "SELECT 1 FROM words GROUP BY lower(english) HAVING count(*) > 1 LIMIT 1"
            ).fetchone()
            return bool(duplicates)
    except sqlite3.DatabaseError:
        return True
