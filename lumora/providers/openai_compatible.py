"""OpenAI-compatible HTTP provider (OpenRouter, OpenAI, vLLM, LM Studio, Together, etc.)."""

from __future__ import annotations

from typing import Any

import httpx

from lumora.exceptions import ProviderError
from lumora.models import Message
from lumora.providers.base import BaseProvider, ProviderChatResult


class OpenAICompatibleProvider(BaseProvider):
    """Works with any service that speaks the OpenAI /chat/completions schema."""

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        key = self.config.resolved_api_key()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        headers.update(self.config.extra_headers or {})
        return headers

    def _url(self) -> str:
        base = self.config.base_url.rstrip("/")
        return f"{base}/chat/completions"

    def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> ProviderChatResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            resp = httpx.post(
                self._url(),
                json=payload,
                headers=self._headers(),
                timeout=timeout or self.config.timeout,
            )
        except httpx.HTTPError as e:
            raise ProviderError(f"HTTP error calling {self.name}: {e}") from e

        if resp.status_code >= 400:
            raise ProviderError(
                f"Provider '{self.name}' returned {resp.status_code}: {resp.text[:500]}",
                status_code=resp.status_code,
            )

        data: dict[str, Any] = resp.json()
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(
                f"Malformed response from '{self.name}': {str(data)[:300]}"
            ) from e

        usage = data.get("usage") or {}
        return ProviderChatResult(
            content=content,
            model=data.get("model", model),
            raw=data,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )
