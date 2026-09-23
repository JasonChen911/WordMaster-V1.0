"""AI providers. Add new providers here without touching the gateway."""

from .deepseek import DeepSeekProvider, PROVIDER_NAME

__all__ = ["DeepSeekProvider", "PROVIDER_NAME"]
