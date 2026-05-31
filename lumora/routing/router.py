"""Heuristic model router."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from lumora.config import ProviderConfig
from lumora.exceptions import ConfigurationError
from lumora.models import Message


Quality = Literal["cheap", "balanced", "smart"]


_COMPLEX_KEYWORDS = re.compile(
    r"\b(architecture|design pattern|refactor|algorithm|prove|theorem|optimi[sz]e|"
    r"security|exploit|vulnerab|threat model|reason|step by step|chain of thought|"
    r"plan(?:ning)?|multi[- ]step|trade[- ]offs?|complexity|big[- ]o|"
    r"derive|integrate|differentiate|matrix|tensor|kubernetes|distributed|"
    r"concurrency|race condition|deadlock)\b",
    re.IGNORECASE,
)

_CODE_HINT = re.compile(r"```|def\s+\w+\(|class\s+\w+|function\s+\w+\(|=>|#include|import\s+\w+")
_MATH_HINT = re.compile(r"(\b\d+\s*[\+\-\*/\^]\s*\d+\b)|\\frac|\\sum|\\int|sigma|integral")


@dataclass
class RouteDecision:
    provider: str
    model: str
    quality: Quality
    reason: str
    routed_to_cheap: bool = False
    routed_to_local: bool = False


class ModelRouter:
    """Picks (provider, model, quality) for each request."""

    def __init__(
        self,
        providers: list[ProviderConfig],
        budget_limit_usd: float | None = None,
    ) -> None:
        if not providers:
            raise ConfigurationError("ModelRouter requires at least one provider.")
        self.providers = providers
        self.budget_limit_usd = budget_limit_usd

    # ------------------------------------------------------------------ helpers

    def _find_provider_with_quality(self, quality: Quality) -> ProviderConfig | None:
        for p in self.providers:
            if quality in p.models:
                return p
        return None

    def _local_provider(self) -> ProviderConfig | None:
        for p in self.providers:
            if p.type == "ollama":
                return p
        return None

    @staticmethod
    def _classify(messages: list[Message]) -> Quality:
        text = "\n".join(m.content for m in messages if m.role in ("user", "system"))
        length = len(text)

        if _COMPLEX_KEYWORDS.search(text) or _CODE_HINT.search(text) or _MATH_HINT.search(text):
            return "smart"
        if length > 1200:
            return "smart"
        if length < 160:
            return "cheap"
        return "balanced"

    # ------------------------------------------------------------------ public

    def route(
        self,
        messages: list[Message],
        explicit_model: str | None = None,
        explicit_quality: Quality | None = None,
        current_spend_usd: float = 0.0,
    ) -> RouteDecision:
        # 1) Explicit model wins.
        if explicit_model:
            for p in self.providers:
                if explicit_model in p.models.values() or explicit_model in p.models:
                    model = p.models.get(explicit_model, explicit_model)
                    return RouteDecision(
                        provider=p.name,
                        model=model,
                        quality=explicit_quality or "balanced",
                        reason="explicit model requested by caller",
                    )
            # Fall back: use first provider with the raw model name.
            p = self.providers[0]
            return RouteDecision(
                provider=p.name,
                model=explicit_model,
                quality=explicit_quality or "balanced",
                reason="explicit model passed through to first provider",
            )

        quality: Quality = explicit_quality or self._classify(messages)

        # 2) Budget pressure: if >= 85% of budget used, downshift.
        if (
            self.budget_limit_usd
            and current_spend_usd >= 0.85 * self.budget_limit_usd
            and quality != "cheap"
        ):
            quality = "cheap"
            reason_prefix = "downshifted to cheap (budget near limit)"
        else:
            reason_prefix = f"classified as {quality}"

        # 3) For cheap quality, prefer a local Ollama if configured.
        if quality == "cheap":
            local = self._local_provider()
            if local and ("cheap" in local.models or local.models):
                model = local.models.get("cheap") or next(iter(local.models.values()))
                return RouteDecision(
                    provider=local.name,
                    model=model,
                    quality="cheap",
                    reason=f"{reason_prefix}; local provider available",
                    routed_to_cheap=True,
                    routed_to_local=True,
                )

        # 4) Find a provider that has the chosen tier.
        chosen = self._find_provider_with_quality(quality)
        if chosen is None:
            # Fall back through tiers in order.
            for fallback in ("balanced", "smart", "cheap"):
                chosen = self._find_provider_with_quality(fallback)  # type: ignore[arg-type]
                if chosen is not None:
                    quality = fallback  # type: ignore[assignment]
                    reason_prefix += f"; fell back to {fallback}"
                    break
        if chosen is None:
            raise ConfigurationError("No provider has any model tier configured.")

        return RouteDecision(
            provider=chosen.name,
            model=chosen.models[quality],
            quality=quality,
            reason=reason_prefix,
            routed_to_cheap=(quality == "cheap"),
            routed_to_local=(chosen.type == "ollama"),
        )
