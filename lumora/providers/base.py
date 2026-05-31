"""Abstract base provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from lumora.config import ProviderConfig
from lumora.models import Message


@dataclass
class ProviderChatResult:
    content: str
    model: str
    raw: dict[str, Any]
    input_tokens: int | None = None
    output_tokens: int | None = None


class BaseProvider(ABC):
    """Abstract provider interface. Adapters implement chat()."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def is_local(self) -> bool:
        return self.config.type == "ollama"

    def resolve_model(self, model: str | None, quality: str | None) -> str:
        if model:
            return model
        if quality and quality in self.config.models:
            return self.config.models[quality]
        if "balanced" in self.config.models:
            return self.config.models["balanced"]
        if self.config.models:
            return next(iter(self.config.models.values()))
        from lumora.exceptions import ConfigurationError

        raise ConfigurationError(
            f"Provider '{self.name}' has no model configured for quality='{quality}'."
        )

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> ProviderChatResult:
        """Send a chat request to the provider."""
