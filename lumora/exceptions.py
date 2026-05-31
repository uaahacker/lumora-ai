"""LumoraAI custom exceptions."""

from __future__ import annotations

import re


_KEY_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"api[_-]?key\"?\s*[:=]\s*\"?[A-Za-z0-9_\-]{10,}\"?", re.IGNORECASE),
]


def redact_secrets(message: str) -> str:
    """Strip likely API keys/tokens from a message before showing to the user."""
    if not message:
        return message
    out = message
    for pat in _KEY_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


class LumoraError(Exception):
    """Base error for all LumoraAI failures. Always redacts secrets."""

    def __init__(self, message: str = "") -> None:
        super().__init__(redact_secrets(message))


class ConfigurationError(LumoraError):
    """Raised when client configuration is invalid."""


class ProviderError(LumoraError):
    """Raised when a provider returns a non-recoverable error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(ProviderError):
    """Raised when retries are exhausted on rate-limited responses."""


class BudgetExceededError(LumoraError):
    """Raised when a request would exceed the configured budget limit."""


class CacheError(LumoraError):
    """Raised when the cache backend cannot be used."""
