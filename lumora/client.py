"""LumoraClient - the unified entry point."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable

from lumora.cache import BaseCache, CacheEntry, SQLiteCache
from lumora.cache.base import hash_key, normalize_messages
from lumora.config import LumoraConfig, ProviderConfig, load_config_from_toml
from lumora.cost import CostTracker, ModelPricing
from lumora.cost.pricing import estimate_tokens
from lumora.enhancement import EnhancementResult, PromptEnhancer
from lumora.exceptions import ConfigurationError, ProviderError
from lumora.models import (
    ChatResponse,
    Message,
    SavingsReport,
    UsageRecord,
    UsageSummary,
)
from lumora.observability import get_logger, new_request_id
from lumora.providers import BaseProvider, build_provider
from lumora.rate_limit import RetryPolicy, with_retries
from lumora.routing import ModelRouter


log = get_logger()


class LumoraClient:
    """Smart, cost-aware client that sits between your app and any LLM provider."""

    def __init__(
        self,
        providers: list[dict[str, Any]] | list[ProviderConfig] | None = None,
        *,
        config: LumoraConfig | None = None,
        config_path: str | Path | None = None,
        cache_enabled: bool = True,
        cache_path: str = ".lumora_cache.sqlite",
        cache_fuzzy: bool = False,
        cache_similarity_threshold: float = 0.92,
        budget_limit_usd: float | None = None,
        enhance_prompt_default: bool = False,
        allow_prompt_logging: bool = False,
        max_retries: int = 3,
        request_timeout: float = 60.0,
        pricing_overrides: dict[str, ModelPricing] | None = None,
        cache_backend: BaseCache | None = None,
    ) -> None:
        # 1) Resolve config from one of: explicit config, TOML file, or kwargs.
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.config = load_config_from_toml(config_path)
        else:
            if not providers:
                raise ConfigurationError(
                    "Pass providers=[...] or config=... or config_path=... to LumoraClient."
                )
            normalized = [
                p if isinstance(p, ProviderConfig) else ProviderConfig(**p)
                for p in providers
            ]
            self.config = LumoraConfig(
                providers=normalized,
                cache_enabled=cache_enabled,
                cache_path=cache_path,
                cache_fuzzy=cache_fuzzy,
                cache_similarity_threshold=cache_similarity_threshold,
                budget_limit_usd=budget_limit_usd,
                enhance_prompt_default=enhance_prompt_default,
                allow_prompt_logging=allow_prompt_logging,
                max_retries=max_retries,
                request_timeout=request_timeout,
            )

        # 2) Build provider instances.
        self._providers: dict[str, BaseProvider] = {
            p.name: build_provider(p) for p in self.config.providers
        }

        # 3) Subsystems.
        self.router = ModelRouter(
            providers=self.config.providers,
            budget_limit_usd=self.config.budget_limit_usd,
        )
        self.cost_tracker = CostTracker(
            budget_limit_usd=self.config.budget_limit_usd,
            pricing_overrides=pricing_overrides,
        )
        self.enhancer = PromptEnhancer()
        self.cache: BaseCache | None = None
        if self.config.cache_enabled:
            self.cache = cache_backend or SQLiteCache(self.config.cache_path)

        self._retry_policy = RetryPolicy(max_retries=self.config.max_retries)

    # ------------------------------------------------------------------ public

    def chat(
        self,
        messages: list[dict[str, str]] | list[Message],
        *,
        model: str | None = None,
        quality: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        use_cache: bool | None = None,
        enhance_prompt: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatResponse:
        request_id = new_request_id()
        started = time.time()
        msgs: list[Message] = [
            m if isinstance(m, Message) else Message(**m) for m in messages
        ]

        # 1) Optional prompt enhancement (last user message only).
        enhancement: EnhancementResult | None = None
        do_enhance = (
            enhance_prompt if enhance_prompt is not None else self.config.enhance_prompt_default
        )
        if do_enhance:
            msgs, enhancement = self._maybe_enhance(msgs)

        # 2) Route.
        decision = self.router.route(
            messages=msgs,
            explicit_model=model,
            explicit_quality=quality,  # type: ignore[arg-type]
            current_spend_usd=self.cost_tracker.total_spend,
        )
        provider = self._providers.get(decision.provider)
        if provider is None:
            raise ConfigurationError(f"Router picked unknown provider '{decision.provider}'.")

        log.info(
            "req=%s route provider=%s model=%s quality=%s reason=%s",
            request_id, decision.provider, decision.model, decision.quality, decision.reason,
        )

        # 3) Cache lookup.
        normalized = normalize_messages(msgs)
        key = hash_key(normalized, decision.model)
        cache_should_use = use_cache if use_cache is not None else self.config.cache_enabled

        if self.cache is not None and cache_should_use:
            hit = self.cache.get_exact(key)
            if hit is None and self.config.cache_fuzzy:
                hit = self.cache.get_fuzzy(normalized, self.config.cache_similarity_threshold)
            if hit is not None:
                return self._build_cache_response(
                    hit, msgs, decision, request_id, started, enhancement
                )

        # 4) Budget pre-check (rough estimate from prompt text).
        prompt_text = "\n".join(m.content for m in msgs)
        est_in = estimate_tokens(prompt_text)
        est_out = max_tokens or max(64, est_in // 2)
        projected = self.cost_tracker.estimate_cost(decision.model, est_in, est_out)
        self.cost_tracker.check_budget(projected)

        # 5) Call provider with retries.
        def _call():
            return provider.chat(
                messages=msgs,
                model=decision.model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.config.request_timeout,
            )

        try:
            result = with_retries(_call, self._retry_policy)
        except ProviderError:
            raise

        # 6) Token + cost accounting (prefer provider-reported usage).
        in_tokens = result.input_tokens if result.input_tokens is not None else est_in
        out_tokens = (
            result.output_tokens
            if result.output_tokens is not None
            else estimate_tokens(result.content)
        )
        cost = self.cost_tracker.estimate_cost(decision.model, in_tokens, out_tokens)

        # 7) Track usage (with reference model for savings if routed down).
        reference_model = self._reference_smart_model() if decision.routed_to_cheap else None
        self.cost_tracker.record(
            UsageRecord(
                request_id=request_id,
                provider=decision.provider,
                model=decision.model,
                quality=decision.quality,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                cost=cost,
                cache_hit=False,
                routed_to_cheap=decision.routed_to_cheap,
                routed_to_local=decision.routed_to_local,
            ),
            reference_model_for_savings=reference_model,
        )

        # 8) Cache store.
        if self.cache is not None and cache_should_use:
            self.cache.put(
                CacheEntry(
                    key=key,
                    normalized_prompt=normalized,
                    response_content=result.content,
                    model=decision.model,
                    provider=decision.provider,
                    created_at=SQLiteCache.now(),
                    metadata=self._safe_meta(metadata),
                )
            )

        latency_ms = int((time.time() - started) * 1000)
        log.info(
            "req=%s done provider=%s model=%s cache_hit=False latency_ms=%d cost=%.6f",
            request_id, decision.provider, decision.model, latency_ms, cost,
        )

        return ChatResponse(
            content=result.content,
            model_used=decision.model,
            provider_used=decision.provider,
            estimated_input_tokens=in_tokens,
            estimated_output_tokens=out_tokens,
            estimated_cost=round(cost, 6),
            cache_hit=False,
            latency_ms=latency_ms,
            request_id=request_id,
            raw_response=result.raw,
        )

    # ------------------------------------------------------------------ reports

    def usage_summary(self) -> UsageSummary:
        return self.cost_tracker.usage_summary()

    def savings_report(self) -> SavingsReport:
        return self.cost_tracker.savings_report()

    def close(self) -> None:
        if self.cache is not None:
            self.cache.close()

    # ------------------------------------------------------------------ helpers

    def _maybe_enhance(self, msgs: list[Message]) -> tuple[list[Message], EnhancementResult | None]:
        for i in range(len(msgs) - 1, -1, -1):
            if msgs[i].role == "user":
                result = self.enhancer.enhance(msgs[i].content)
                if result.changed:
                    new = list(msgs)
                    new[i] = Message(role="user", content=result.enhanced_prompt)
                    return new, result
                return msgs, result
        return msgs, None

    def _reference_smart_model(self) -> str | None:
        """Pick the smartest configured model to compute routing savings against."""
        for tier in ("smart", "balanced"):
            for p in self.config.providers:
                if tier in p.models:
                    return p.models[tier]
        return None

    @staticmethod
    def _safe_meta(metadata: dict[str, Any] | None) -> dict[str, Any]:
        if not metadata:
            return {}
        return {
            k: v
            for k, v in metadata.items()
            if "key" not in k.lower() and "token" not in k.lower() and "secret" not in k.lower()
        }

    def _build_cache_response(
        self,
        hit: CacheEntry,
        msgs: list[Message],
        decision,
        request_id: str,
        started: float,
        enhancement: EnhancementResult | None,
    ) -> ChatResponse:
        in_tokens = estimate_tokens("\n".join(m.content for m in msgs))
        out_tokens = estimate_tokens(hit.response_content)
        # Saved = what calling decision.model would have cost.
        self.cost_tracker.record(
            UsageRecord(
                request_id=request_id,
                provider=hit.provider,
                model=hit.model,
                quality=decision.quality,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                cost=0.0,
                cache_hit=True,
                routed_to_cheap=decision.routed_to_cheap,
                routed_to_local=decision.routed_to_local,
            ),
            reference_model_for_savings=decision.model,
        )
        latency_ms = int((time.time() - started) * 1000)
        log.info(
            "req=%s done provider=%s model=%s cache_hit=True latency_ms=%d",
            request_id, hit.provider, hit.model, latency_ms,
        )
        return ChatResponse(
            content=hit.response_content,
            model_used=hit.model,
            provider_used=hit.provider,
            estimated_input_tokens=in_tokens,
            estimated_output_tokens=out_tokens,
            estimated_cost=0.0,
            cache_hit=True,
            latency_ms=latency_ms,
            request_id=request_id,
            raw_response=None,
        )

    # Allow iteration over configured providers (handy for debugging).
    def __iter__(self) -> Iterable[str]:
        return iter(self._providers.keys())
