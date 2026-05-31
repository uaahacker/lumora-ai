"""Abstract cache interface. SQLite today; Redis/Postgres later."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from lumora.models import Message


@dataclass
class CacheEntry:
    key: str
    normalized_prompt: str
    response_content: str
    model: str
    provider: str
    created_at: float
    metadata: dict[str, Any]


def normalize_messages(messages: list[Message]) -> str:
    """Normalize chat messages for stable cache keys."""
    parts = []
    for m in messages:
        text = " ".join(m.content.split()).strip().lower()
        parts.append(f"{m.role}:{text}")
    return "\n".join(parts)


def hash_key(normalized: str, model_hint: str = "") -> str:
    h = hashlib.sha256()
    h.update(normalized.encode("utf-8"))
    if model_hint:
        h.update(b"::")
        h.update(model_hint.encode("utf-8"))
    return h.hexdigest()


class BaseCache(ABC):
    """Abstract cache. Implementations must be safe to call concurrently from one process."""

    @abstractmethod
    def get_exact(self, key: str) -> CacheEntry | None: ...

    @abstractmethod
    def get_fuzzy(self, normalized_prompt: str, threshold: float) -> CacheEntry | None: ...

    @abstractmethod
    def put(self, entry: CacheEntry) -> None: ...

    @abstractmethod
    def clear(self) -> int: ...

    @abstractmethod
    def stats(self) -> dict[str, Any]: ...

    def close(self) -> None:  # pragma: no cover - default no-op
        return None

    @staticmethod
    def serialize_metadata(meta: dict[str, Any]) -> str:
        # Never serialize keys named like secrets.
        safe = {k: v for k, v in meta.items() if "key" not in k.lower() and "token" not in k.lower()}
        return json.dumps(safe, default=str)

    @staticmethod
    def deserialize_metadata(blob: str) -> dict[str, Any]:
        if not blob:
            return {}
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return {}
