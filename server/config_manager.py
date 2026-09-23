"""
Secure user configuration storage.
API keys stored via Windows Credential Manager (keyring).
Non-sensitive config stored in user_data/config.json.
"""

import json
import os
import sys
from pathlib import Path

import keyring

HERE = Path(__file__).resolve().parent  # server/
PROJECT = HERE.parent

if getattr(sys, "frozen", False):
    CONFIG_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "WordMaster" / "user_data"
else:
    CONFIG_DIR = PROJECT / "user_data"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"

# keyring service name for Windows Credential Manager
_KEYRING_SERVICE = "WordMaster/DeepSeek"
_KEYRING_USERNAME = "api_key"

DEFAULT_API_BASE = "https://api.deepseek.com/v1"


def load_config() -> dict:
    """Load user configuration."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict):
    """Save user configuration."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(CONFIG_PATH)


# ═══════════════════════════════════════════════════════════════════
#  API Key resolution
#
#  A user's own DeepSeek API key is the ONLY credential the app uses by
#  default. It is stored in the Windows Credential Manager (keyring) and is
#  never logged, returned to the frontend, or written to disk.
#
#  Advanced users may additionally provide a default key via the
#  WORDMASTER_DEFAULT_API_KEY environment variable (e.g. for a deployment
#  scenario); that value takes precedence only when no per-user key exists.
#  No key is ever embedded in the source code or the packaged binary.
# ═══════════════════════════════════════════════════════════════════

_DEFAULT_KEY_ENV = "WORDMASTER_DEFAULT_API_KEY"

# Placeholder strings that must never be treated as a real credential.
_PLACEHOLDER_KEYS = (
    "",
    "your-key-here",
    "your-api-key-here",
    "sk-xxx",
    "sk-your-key-here",
    "sk-your-api-key-here",
    "sk-your-deepseek-key-here",
)


def _is_placeholder(key: str) -> bool:
    """True if the value is empty or a placeholder, not a real credential."""
    return (key or "").strip().lower() in _PLACEHOLDER_KEYS


def get_user_api_key() -> str:
    """Get the user's own API key from Windows Credential Manager (keyring)."""
    try:
        key = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        if key and key.strip() and not _is_placeholder(key):
            return key.strip()
    except Exception:
        pass
    return ""


def get_default_api_key() -> str:
    """Get an optional deployment default key from the environment.

    This is NOT an embedded key — it only reads the WORDMASTER_DEFAULT_API_KEY
    environment variable. Returns "" when unset.
    """
    key = os.getenv(_DEFAULT_KEY_ENV, "")
    if not _is_placeholder(key):
        return key.strip()
    return ""


def get_deepseek_api_key() -> str:
    """Resolve the effective DeepSeek API key.

    Priority:
    1. User's own key (keyring) — always wins.
    2. WORDMASTER_DEFAULT_API_KEY env var.
    3. None.
    """
    user_key = get_user_api_key()
    if user_key:
        return user_key

    return get_default_api_key()


def set_deepseek_api_key(key: str):
    """Save (or clear) the user's own DeepSeek API key in Windows Credential Manager."""
    if key:
        try:
            keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, key.strip())
        except Exception:
            raise RuntimeError(
                "无法访问 Windows 凭据管理器，API Key 保存失败。"
                "请确认系统凭据服务正常运行。"
            )
    else:
        # Delete key from keyring
        try:
            keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        except Exception:
            pass  # Already deleted or not found


def get_deepseek_api_base() -> str:
    """Get DeepSeek API base URL (normalized: no trailing slash)."""
    env_base = os.getenv("DEEPSEEK_API_BASE", "").strip()
    if env_base:
        return env_base.rstrip("/")
    config = load_config()
    base = config.get("deepseek_api_base", DEFAULT_API_BASE)
    return (base or DEFAULT_API_BASE).strip().rstrip("/") or DEFAULT_API_BASE


def set_deepseek_api_base(base: str):
    """Save DeepSeek API base URL."""
    config = load_config()
    config["deepseek_api_base"] = base.strip().rstrip("/")
    save_config(config)


def has_user_api_key() -> bool:
    """True if the user has configured their own key in the keyring."""
    return bool(get_user_api_key())


def using_default_credential() -> bool:
    """True if AI is running on an env-provided default credential (no user key)."""
    return (not get_user_api_key()) and bool(get_default_api_key())


def is_ai_configured() -> bool:
    """True if the AI service is usable (user key or env-provided key present)."""
    key = get_deepseek_api_key()
    return bool(key and len(key) > 10)


def get_config_status() -> dict:
    """Configuration status for the frontend.

    Exposes only availability flags — never key content, prefix, suffix,
    preview, or the full key.
    """
    return {
        "configured": has_user_api_key(),
        "available": is_ai_configured(),
        "using_default": using_default_credential(),
        "api_base": get_deepseek_api_base(),
    }
