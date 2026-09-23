"""AI Gateway — unified LLM access with retry, JSON schema validation, logging.

Design:
- ``chat_completion`` → raw text, with one automatic retry on transient errors.
- ``chat_json`` → validated structured output: parse → pydantic-validate →
  repair → retry → fallback. It never returns a raw string for structured work.
- Token usage is logged for observability; no provider key is ever logged.
"""

import json
import logging
import re
from typing import Optional, Type, TypeVar, get_origin

from config_manager import get_deepseek_api_key

from .providers import DeepSeekProvider

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_configured() -> bool:
    key = get_deepseek_api_key()
    return bool(key) and len(key) > 10


def get_status() -> dict:
    from .providers.deepseek import model_name
    return {
        "available": is_configured(),
        "model": model_name() if is_configured() else None,
        "provider": "deepseek",
    }


# ─────────────────────────────────────────────────────────────────
#  Raw completion (with retry)
# ─────────────────────────────────────────────────────────────────

async def chat_completion(
    messages: list[dict],
    *,
    temperature: float = 0.7,
    max_tokens: int = 800,
    timeout: float | None = None,
    retries: int = 1,
) -> dict:
    """One raw chat-completion with a single automatic retry on transient errors.

    Returns {"content", "error", "status", "usage"}; exactly one of content/error.
    """
    if not is_configured():
        return {
            "content": None,
            "error": "AI 服务未配置，请先在 设置 → AI 服务 中配置 API Key。",
            "status": None,
            "usage": None,
        }

    effective_timeout = timeout if timeout is not None else 30.0
    last = None
    for attempt in range(retries + 1):
        last = await DeepSeekProvider.complete(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=effective_timeout,
        )
        if last.get("content") is not None:
            _log_usage(messages, last)
            return last
        # Retry only transient failures (timeouts, 5xx); not auth/quota errors.
        if not _is_retryable(last):
            break
        if attempt < retries:
            logger.info("AI retry %d/%d after: %s", attempt + 1, retries, last.get("error"))
    return last or {"content": None, "error": "AI 请求失败。", "status": None, "usage": None}


def _is_retryable(result: dict) -> bool:
    status = result.get("status")
    return status is None or status >= 500 or status == 429


def _log_usage(messages: list[dict], result: dict) -> None:
    usage = result.get("usage") or {}
    tokens = usage.get("total_tokens")
    if tokens:
        logger.info("AI tokens: total=%s (prompt=%s completion=%s)",
                    tokens, usage.get("prompt_tokens"), usage.get("completion_tokens"))


# ─────────────────────────────────────────────────────────────────
#  Structured JSON completion (with schema validation)
# ─────────────────────────────────────────────────────────────────

def _strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if not text.startswith("```"):
        return text
    lines = text.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json(raw: str):
    """Parse JSON from a model response, handling code fences and stray text."""
    if not raw:
        return None
    clean = _strip_code_fence(raw)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", raw):
        try:
            return decoder.raw_decode(raw, match.start())[0]
        except json.JSONDecodeError:
            continue
    return None


async def chat_json(
    messages: list[dict],
    schema: Type[T],
    *,
    temperature: float = 0.4,
    max_tokens: int = 1200,
    timeout: float | None = None,
    retries: int = 1,
) -> Optional[T]:
    """Structured output with parse → validate → repair → retry → fallback.

    Returns a validated ``schema`` instance, or None when the model could not
    produce valid data after retries (the caller supplies a safe fallback).
    """
    if not is_configured():
        return None

    for attempt in range(retries + 1):
        result = await chat_completion(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            retries=0,  # retry loop is handled here, around parsing
        )
        raw = result.get("content")
        if raw is None:
            if not _is_retryable(result):
                return None
            continue

        data = _extract_json(raw)
        if data is None:
            logger.warning("AI returned non-JSON; attempt %d", attempt + 1)
            if attempt < retries:
                messages = _add_retry_hint(messages)
                continue
            return None

        parsed = _validate(schema, data)
        if parsed is not None:
            return parsed

        # Repair: coerce the raw data through a lenient pass and re-validate.
        repaired = _repair(schema, data)
        if repaired is not None:
            return repaired

        logger.warning("AI JSON failed schema validation; attempt %d", attempt + 1)
        if attempt < retries:
            messages = _add_retry_hint(messages)
            continue
        return None

    return None


def _validate(schema: Type[T], data) -> Optional[T]:
    try:
        return schema.model_validate(data)
    except Exception:
        return None


def _repair(schema: Type[T], data) -> Optional[T]:
    """Coerce common model mistakes (a bare list where an object was expected)."""
    try:
        if isinstance(data, dict):
            return schema.model_validate(data)
        if isinstance(data, list):
            # Wrap the bare list under the schema's first list-typed field.
            for name, field in schema.model_fields.items():
                if get_origin(field.annotation) is list:
                    return schema.model_validate({name: data})
        return None
    except Exception:
        return None


def _add_retry_hint(messages: list[dict]) -> list[dict]:
    hint = {
        "role": "user",
        "content": "你上一次的输出不是合法的 JSON，或不符合要求的字段结构。请只输出符合要求的纯 JSON，不要任何解释。",
    }
    return messages + [hint]
