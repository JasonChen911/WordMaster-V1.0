"""
WordManager — JSON-based word bank + user progress storage.

## Data layout

    内置词库请勿删除/       ← read-only word banks
        CET4.json
        CET6.json
        高中.json
        ...

    user_data/              ← per-book user progress
        CET4_progress.json
        CET6_progress.json
        settings.json       ← active book, daily goal

## Word bank JSON schema

    [
        {
            "word": "abandon",
            "meaning": "放弃；抛弃",
            "example": "He decided to abandon his plan.",
            "translation": "他决定放弃旅行计划。",
            "illustration": "abandon.svg"
        }
    ]

## Progress JSON schema

    {
        "abandon": {
            "status": "new|learning|mastered",
            "review_count": 0,
            "last_review": "2026-08-07T14:00:00",
            "next_review": "2026-08-08T14:00:00"
        }
    }

Words NOT in progress file are treated as status="new".
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent  # server/

if getattr(sys, "frozen", False):
    BUNDLE = Path(sys._MEIPASS)
    WORD_BANK_DIR = BUNDLE / "内置词库请勿删除"
    USER_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "WordMaster" / "user_data"
else:
    PROJECT = HERE.parent
    WORD_BANK_DIR = PROJECT / "内置词库请勿删除"
    USER_DATA_DIR = PROJECT / "user_data"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ebbinghaus intervals in hours
INTERVALS = {0: 4, 1: 24, 2: 48, 3: 96, 4: 168, 5: 360, 6: 720}


# ═══════════════════════════════════════════════════════════════════
#  Word bank (read-only)
# ═══════════════════════════════════════════════════════════════════

def _list_word_banks() -> list[Path]:
    if not WORD_BANK_DIR.exists():
        return []
    return sorted(WORD_BANK_DIR.glob("*.json"))


def get_book_list() -> list[dict]:
    """Return list of available word books."""
    books = []
    for path in _list_word_banks():
        name = path.stem
        data = _load_json(path)
        books.append({
            "id": name,
            "book_name": name,
            "word_count": len(data) if data else 0,
            "file_name": path.name,
            "is_active": _get_active_book() == name,
            "is_builtin": True,
        })
    return books


def _load_json(path: Path) -> list | dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if str(path).endswith(".json") and WORD_BANK_DIR in path.parents else {}


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def get_word_bank(book_id: str) -> list[dict]:
    """Read a word bank JSON file. Returns list of {word, meaning, example, translation, illustration}."""
    path = WORD_BANK_DIR / f"{book_id}.json"
    return _load_json(path) or []


def get_word_bank_map(book_id: str) -> dict[str, dict]:
    """Word bank as {word_lower: entry} dict for fast lookup."""
    entries = get_word_bank(book_id)
    return {e["word"].lower(): e for e in entries}


# ═══════════════════════════════════════════════════════════════════
#  User progress
# ═══════════════════════════════════════════════════════════════════

def _progress_path(book_id: str) -> Path:
    return USER_DATA_DIR / f"{book_id}_progress.json"


def get_progress(book_id: str) -> dict[str, dict]:
    """Get user progress for a book. Returns {word_lower: {status, review_count, ...}}."""
    return _load_json(_progress_path(book_id)) or {}


def save_progress(book_id: str, progress: dict[str, dict]):
    """Save user progress for a book."""
    _save_json(_progress_path(book_id), progress)


def update_word_progress(book_id: str, word: str, result: str):
    """Record a study result. Updates proficiency, review schedule, and study time."""
    progress = get_progress(book_id)
    now = datetime.now()
    key = word.lower()

    entry = progress.get(key, {
        "status": "new",
        "review_count": 0,
        "proficiency": 0,     # 0=new 1=learning 2=fuzzy 3=familiar 4=mastered
        "last_review": None,
        "next_review": None,
    })

    entry["review_count"] = entry.get("review_count", 0) + 1
    entry["last_review"] = now.isoformat()
    prof = entry.get("proficiency", 0)

    # ── Proficiency + next_review ──
    if result == "too_easy" or result == "know":
        # Correct → advance proficiency, longer interval
        entry["proficiency"] = min(4, prof + 1)
        entry["status"] = "mastered" if entry["proficiency"] >= 4 else "learning"
        entry["next_review"] = (now + timedelta(days=3)).isoformat()
    elif result == "fuzzy":
        # Almost → stay or slight degrade, review tomorrow
        entry["proficiency"] = max(1, prof - 1)
        entry["status"] = "learning"
        entry["next_review"] = (now + timedelta(days=1)).isoformat()
    else:  # unknown
        # Wrong → reset, review tomorrow with priority
        entry["proficiency"] = max(1, prof - 2)
        entry["status"] = "learning"
        entry["next_review"] = (now + timedelta(days=1)).isoformat()

    # First-time study always → learning
    if entry["review_count"] == 1:
        entry["status"] = "learning"
        entry["proficiency"] = 1

    # Track study session time
    _track_study_time(1)

    progress[key] = entry
    save_progress(book_id, progress)

    return entry


# ═══════════════════════════════════════════════════════════════════
#  Study time tracking
# ═══════════════════════════════════════════════════════════════════

_STUDY_HISTORY_PATH = USER_DATA_DIR / "study_history.json"


def _track_study_time(minutes: int = 1):
    """Increment today's study minutes."""
    today = datetime.now().strftime("%Y-%m-%d")
    history = _load_json(_STUDY_HISTORY_PATH) or {}
    history[today] = history.get(today, 0) + minutes
    _save_json(_STUDY_HISTORY_PATH, history)


def get_today_study_minutes() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    history = _load_json(_STUDY_HISTORY_PATH) or {}
    return history.get(today, 0)


def reset_progress(book_id: str):
    """Reset all progress for a book."""
    _save_json(_progress_path(book_id), {})


def get_progress_stats(book_id: str) -> dict:
    """Get summary stats for a book, including proficiency and study time."""
    progress = get_progress(book_id)
    total = len(get_word_bank(book_id))
    now = datetime.now()

    new_count = 0
    learning_count = 0
    mastered_count = 0
    review_due = 0
    studied = 0
    prof_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

    for e in progress.values():
        prof = e.get("proficiency", 0)
        prof_dist[prof] = prof_dist.get(prof, 0) + 1

        if prof >= 4 or e.get("status") == "mastered":
            mastered_count += 1
        elif prof >= 1 or e.get("review_count", 0) > 0:
            learning_count += 1
        else:
            new_count += 1

        if e.get("review_count", 0) > 0:
            studied += 1

        nr = e.get("next_review")
        if nr and e.get("review_count", 0) > 0:
            try:
                if datetime.fromisoformat(nr) <= now:
                    review_due += 1
            except (ValueError, TypeError):
                pass

    # Words in bank but NOT in progress → implicit new (proficiency 0)
    bank_words = {e["word"].lower() for e in get_word_bank(book_id)}
    tracked = set(progress.keys())
    implicit_new = len(bank_words - tracked)
    new_count += implicit_new
    prof_dist[0] = prof_dist.get(0, 0) + implicit_new

    today_minutes = get_today_study_minutes()

    return {
        "total": total,
        "new": new_count,
        "learning": learning_count,
        "mastered": mastered_count,
        "studied": studied,
        "review_due": review_due,
        "today_minutes": today_minutes,
        "proficiency": prof_dist,
    }


# ═══════════════════════════════════════════════════════════════════
#  Study queue generation
# ═══════════════════════════════════════════════════════════════════

def generate_study_queue(book_id: str, count: int = 20) -> list[dict]:
    """Generate a study queue for a book.

    Priority:
      1. Review-due words (status=learning, next_review <= now)
      2. New words (status=new, never studied)
      3. Fill with remaining learning words if still short

    Returns list of {word, meaning, phonetic, example_en, example_cn, illustration, ...}
    """
    word_bank = get_word_bank_map(book_id)
    progress = get_progress(book_id)
    now = datetime.now()

    queue: list[dict] = []
    used_words: set[str] = set()

    # ── Priority 1: Review-due ──
    review_words = []
    for w_lower, entry in sorted(progress.items(), key=lambda x: x[1].get("next_review", "")):
        if len(review_words) >= count:
            break
        if entry.get("status") != "learning":
            continue
        nr = entry.get("next_review")
        if not nr:
            continue
        nr_dt = datetime.fromisoformat(nr)
        if nr_dt <= now:
            bank_entry = word_bank.get(w_lower)
            if bank_entry and w_lower not in used_words:
                used_words.add(w_lower)
                review_words.append(_make_word_dict(bank_entry, entry))

    queue.extend(review_words)

    # ── Priority 2: New (unstudied) words ──
    if len(queue) < count:
        needed = count - len(queue)
        new_words = []
        # Iterate word bank in order; pick words NOT in progress or with review_count=0
        for entry in get_word_bank(book_id):
            if len(new_words) >= needed:
                break
            w_lower = entry["word"].lower()
            if w_lower in used_words:
                continue
            prog = progress.get(w_lower)
            if prog is None or prog.get("review_count", 0) == 0:
                # Either never studied or has status=new with no actual review
                used_words.add(w_lower)
                new_words.append(_make_word_dict(entry, prog or {"status": "new"}))

        queue.extend(new_words)

    # ── Priority 3: Any remaining learning words as fill ──
    if len(queue) < count:
        needed = count - len(queue)
        for w_lower, prog in sorted(progress.items(), key=lambda x: x[1].get("next_review", "")):
            if len(queue) >= count:
                break
            if w_lower in used_words:
                continue
            bank_entry = word_bank.get(w_lower)
            if bank_entry:
                used_words.add(w_lower)
                queue.append(_make_word_dict(bank_entry, prog))

    return queue


def _make_word_dict(bank_entry: dict, progress_entry: dict | None) -> dict:
    """Merge word bank data with progress data into a single dict for the frontend.
    Prefers AI-cached content over static examples.
    """
    prog = progress_entry or {}
    word_text = bank_entry["word"].lower()

    return {
        "english": bank_entry["word"],
        "phonetic": "",
        "chinese": bank_entry.get("meaning", ""),
        "example_en": bank_entry.get("example", ""),
        "example_cn": bank_entry.get("translation", ""),
        "memory_tip": bank_entry.get("memory_tip", bank_entry.get("tip", "")),
        "ai_source": "static",
        "context": bank_entry.get("context", ""),
        "study_status": prog.get("status", "new"),
        "review_count": prog.get("review_count", 0),
        "review_stage": 0,
        "difficulty": 2.5,
        "is_favorite": False,
        "is_mastered": prog.get("status") == "mastered",
        "accuracy_rate": 0.0,
        "proficiency": 0,
        "next_review": prog.get("next_review"),
        "last_reviewed_at": prog.get("last_review"),
    }


# ═══════════════════════════════════════════════════════════════════
#  Settings
# ═══════════════════════════════════════════════════════════════════

SETTINGS_PATH = USER_DATA_DIR / "settings.json"


def _get_active_book() -> str:
    settings = _load_json(SETTINGS_PATH) or {}
    return settings.get("active_book", "")


def get_active_book() -> dict | None:
    """Get the currently active book info."""
    book_id = _get_active_book()
    books = get_book_list()
    for b in books:
        if b["id"] == book_id:
            return b
    # Auto-select first available
    if books:
        set_active_book(books[0]["id"])
        return books[0]
    return None


def set_active_book(book_id: str):
    """Set the active word book."""
    settings = _load_json(SETTINGS_PATH) or {}
    settings["active_book"] = book_id
    _save_json(SETTINGS_PATH, settings)


def get_settings() -> dict:
    return _load_json(SETTINGS_PATH) or {}


# ═══════════════════════════════════════════════════════════════════
#  Global stats (dashboard-compatible)
# ═══════════════════════════════════════════════════════════════════

def get_global_stats() -> dict:
    """Get global learning stats across all books."""
    books = get_book_list()
    total_words = sum(b["word_count"] for b in books)
    total_studied = 0
    total_mastered = 0

    for b in books:
        stats = get_progress_stats(b["id"])
        total_studied += stats["studied"]
        total_mastered += stats["mastered"]

    return {
        "total_words": total_words,
        "total_studied": total_studied,
        "total_mastered": total_mastered,
        "book_count": len(books),
    }
