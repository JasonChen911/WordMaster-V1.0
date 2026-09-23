"""AI Gateway — the single entry point for every LLM call in WordMaster.

No router talks to DeepSeek directly. They import from here (or from
``ai.services``), so model/key/timeout/retry/JSON/logging/cache/token-usage are
handled in one place.
"""

from .gateway import (
    chat_completion,
    chat_json,
    is_configured,
    get_status,
)

__all__ = [
    "chat_completion",
    "chat_json",
    "is_configured",
    "get_status",
]
