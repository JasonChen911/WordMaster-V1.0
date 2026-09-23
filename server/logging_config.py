"""Centralized logging configuration for WordMaster."""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: Path = None, level: int = logging.INFO):
    """Configure logging with console and file handlers.

    Args:
        log_dir: Directory for log files. Defaults to server/logs/
        level: Logging level. Defaults to INFO.
    """
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # File handler with rotation (max 5MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        log_dir / "wordmaster.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Error file handler
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)
    root.addHandler(error_handler)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    return root


def startup_log(message: str) -> None:
    """Append one lightweight line to %APPDATA%\\WordMaster\\logs\\startup.log.

    Used by the desktop launcher to record startup phases, DB/migration status,
    port state and error types. Size-capped to avoid unbounded growth and never
    records API keys, passwords or request contents.
    """
    try:
        from datetime import datetime

        data_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "WordMaster"
        log_path = data_dir / "logs" / "startup.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Rotate out the previous file once it grows beyond 256 KB.
        if log_path.exists() and log_path.stat().st_size > 256 * 1024:
            old = log_path.with_suffix(".old")
            try:
                old.unlink(missing_ok=True)
            except Exception:
                pass
            log_path.rename(old)

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")
    except Exception:
        # Startup logging must never break startup.
        pass
