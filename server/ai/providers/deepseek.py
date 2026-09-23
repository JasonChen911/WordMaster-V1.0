"""DeepSeek provider — the concrete OpenAI-compatible chat client.

Only this module knows DeepSeek's URL shape and headers. Everything else goes
through the gateway, which resolves credentials from ``config_manager``.
"""

import logging

import httpx

from config_manager import get_deepseek_api_key, get_deepseek_api_base

logger = logging.getLogger(__name__)

PROVIDER_NAME = "deepseek"
DEFAULT_API_BASE = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"


class DeepSeekProvider:
    """Stateless DeepSeek chat-completions client."""

    name = PROVIDER_NAME

    @staticmethod
    def api_base() -> str:
        return (get_deepseek_api_base() or DEFAULT_API_BASE).rstrip("/")

    @staticmethod
    def api_key() -> str:
        return get_deepseek_api_key()

    @staticmethod
    def model_name() -> str:
        import os
        return os.environ.get("AI_MODEL", DEFAULT_MODEL)

    @staticmethod
    def chat_url() -> str:
        return f"{DeepSeekProvider.api_base()}/chat/completions"

    @staticmethod
    async def complete(
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int = 800,
        timeout: float = 30,
        api_key_value: str | None = None,
    ) -> dict:
        """Send one chat-completion request. Returns a normalized result dict.

        Returns exactly one of ``content`` / ``error`` populated.
        """
        key = api_key_value or DeepSeekProvider.api_key()
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": DeepSeekProvider.model_name(),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(DeepSeekProvider.chat_url(), headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices") or []
                    content = ""
                    if choices:
                        content = (choices[0].get("message") or {}).get("content") or ""
                    content = content.strip()
                    usage = data.get("usage") or {}
                    if not content:
                        return {"content": None, "error": "AI 返回了空内容，请重试。", "status": 200, "usage": usage}
                    return {"content": content, "error": None, "status": 200, "usage": usage}

                status = resp.status_code
                message = {
                    401: "API Key 无效，请检查设置。",
                    402: "API 余额不足，请充值。",
                    429: "请求过于频繁，请稍后重试。",
                }.get(status, None)
                if message is None and status >= 500:
                    message = f"DeepSeek 服务暂时不可用 (HTTP {status})，请稍后重试。"
                if message is None:
                    message = f"API 错误 (HTTP {status})，请稍后重试。"
                return {"content": None, "error": message, "status": status, "usage": None}

        except httpx.TimeoutException:
            logger.error(f"DeepSeek timeout after {timeout}s")
            return {"content": None, "error": f"请求超时（>{timeout} 秒），请稍后重试。", "status": None, "usage": None}
        except httpx.ConnectError:
            logger.error("DeepSeek connection error")
            return {"content": None, "error": "无法连接到 API 服务器，请检查网络。", "status": None, "usage": None}
        except Exception as e:  # noqa: BLE001
            logger.error(f"DeepSeek unexpected error: {type(e).__name__}: {e}")
            return {"content": None, "error": f"连接失败：{str(e)[:80]}", "status": None, "usage": None}
