"""Provider adapters for LumoraAI."""

from lumora.providers.base import BaseProvider, ProviderChatResult
from lumora.providers.openai_compatible import OpenAICompatibleProvider
from lumora.providers.ollama import OllamaProvider

__all__ = [
    "BaseProvider",
    "ProviderChatResult",
    "OpenAICompatibleProvider",
    "OllamaProvider",
]


def build_provider(cfg) -> BaseProvider:
    """Factory: build a provider instance from a ProviderConfig."""
    if cfg.type == "openai_compatible":
        return OpenAICompatibleProvider(cfg)
    if cfg.type == "ollama":
        return OllamaProvider(cfg)
    from lumora.exceptions import ConfigurationError

    raise ConfigurationError(f"Unknown provider type: {cfg.type}")
