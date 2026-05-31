"""Ollama local-model provider (http://localhost:11434/api/chat)."""

from __future__ import annotations

from typing import Any

import httpx

from lumora.exceptions import ProviderError
from lumora.models import Message
from lumora.providers.base import BaseProvider, ProviderChatResult


class OllamaProvider(BaseProvider):
    """Adapter for the local Ollama chat API."""

    DEFAULT_BASE_URL = "http://localhost:11434"

    def _url(self) -> str:
        base = (self.config.base_url or self.DEFAULT_BASE_URL).rstrip("/")
        return f"{base}/api/chat"

    def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> ProviderChatResult:
        # Strip optional "ollama/" prefix that may appear in routing configs.
        ollama_model = model.split("ollama/", 1)[-1] if model.startswith("ollama/") else model

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload: dict[str, Any] = {
            "model": ollama_model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": options,
        }

        try:
            resp = httpx.post(
                self._url(),
                json=payload,
                timeout=timeout or self.config.timeout,
            )
        except httpx.HTTPError as e:
            raise ProviderError(f"HTTP error calling Ollama: {e}") from e

        if resp.status_code >= 400:
            raise ProviderError(
                f"Ollama returned {resp.status_code}: {resp.text[:500]}",
                status_code=resp.status_code,
            )

        data: dict[str, Any] = resp.json()
        message = data.get("message") or {}
        content = message.get("content", "")
        return ProviderChatResult(
            content=content,
            model=data.get("model", ollama_model),
            raw=data,
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
        )
