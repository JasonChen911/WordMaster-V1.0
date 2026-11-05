"""Per-user data paths shared by the desktop launcher and backend."""

import os
from pathlib import Path


def user_data_dir(platform: str | None = None) -> Path:
    override = os.getenv("WORDMASTER_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if (platform or os.name) == "nt":
        base = os.getenv("APPDATA")
        return Path(base) / "WordMaster" if base else Path.home() / "AppData" / "Roaming" / "WordMaster"
    base = os.getenv("XDG_DATA_HOME")
    return Path(base) / "WordMaster" if base else Path.home() / ".local" / "share" / "WordMaster"
