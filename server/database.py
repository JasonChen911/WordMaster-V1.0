import os
import shutil
import sys
from pathlib import Path

from sqlalchemy import create_engine, event as sqlalchemy_event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from platform_paths import user_data_dir

# Determine data directory — works for tests, development and PyInstaller.
data_dir_override = os.getenv("WORDMASTER_DATA_DIR")
if data_dir_override or getattr(sys, 'frozen', False) or os.name != 'nt':
    DATA_DIR = user_data_dir()
else:
    DATA_DIR = Path(__file__).resolve().parent

DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "wordmaster.db"

# Ship a clean, pre-initialized database for fast first launch. It is copied to
# AppData only when the user has no database yet; existing user data is never
# overwritten.
if (getattr(sys, "frozen", False) or data_dir_override) and not DATABASE_PATH.exists():
    bundle_root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    bundled_seed = bundle_root / "server" / "wordmaster_seed.db"
    if bundled_seed.exists():
        shutil.copy2(bundled_seed, DATABASE_PATH)

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# WAL mode + a generous busy timeout keep the app responsive under concurrent
# read+write (the Dashboard polls every few seconds while the Study page writes).
# check_same_thread=False is required because FastAPI requests run in a threadpool.
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@sqlalchemy_event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL + synchronous=NORMAL for concurrent-reader/single-writer safety."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
