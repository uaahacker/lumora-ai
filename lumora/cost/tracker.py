"""In-process cost and savings tracker."""

from __future__ import annotations

import threading
from typing import Iterable

from lumora.cost.pricing import ModelPricing, get_pricing
from lumora.exceptions import BudgetExceededError
from lumora.models import SavingsReport, UsageRecord, UsageSummary


class CostTracker:
    """Tracks spend, savings from cache, and savings from routing decisions."""

    def __init__(
        self,
        budget_limit_usd: float | None = None,
        pricing_overrides: dict[str, ModelPricing] | None = None,
    ) -> None:
        self.budget_limit_usd = budget_limit_usd
        self.pricing_overrides = pricing_overrides or {}
        self._records: list[UsageRecord] = []
        self._saved_from_cache_usd: float = 0.0
        self._saved_from_routing_usd: float = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------ pricing API

    def price_of(self, model: str) -> ModelPricing:
        return get_pricing(model, self.pricing_overrides)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        return self.price_of(model).cost(input_tokens, output_tokens)

    # ------------------------------------------------------------ budget API

    @property
    def total_spend(self) -> float:
        with self._lock:
            return sum(r.cost for r in self._records if not r.cache_hit)

    def check_budget(self, projected_cost: float) -> None:
        if self.budget_limit_usd is None:
            return
        if self.total_spend + projected_cost > self.budget_limit_usd:
            raise BudgetExceededError(
                f"Request would exceed budget_limit_usd="
                f"{self.budget_limit_usd:.4f}; current spend="
                f"{self.total_spend:.4f}, projected add={projected_cost:.4f}."
            )

    # ------------------------------------------------------------ record API

    def record(
        self,
        record: UsageRecord,
        reference_model_for_savings: str | None = None,
    ) -> None:
        with self._lock:
            self._records.append(record)
            if record.cache_hit:
                # Money saved = what the call WOULD have cost without cache.
                ref = reference_model_for_savings or record.model
                price = self.price_of(ref)
                saved = price.cost(record.input_tokens, record.output_tokens)
                self._saved_from_cache_usd += saved
            elif reference_model_for_savings and reference_model_for_savings != record.model:
                # Money saved by downshifting from a more expensive model.
                expensive = self.price_of(reference_model_for_savings)
                actual = self.price_of(record.model)
                delta = (
                    expensive.cost(record.input_tokens, record.output_tokens)
                    - actual.cost(record.input_tokens, record.output_tokens)
                )
                if delta > 0:
                    self._saved_from_routing_usd += delta

    def records(self) -> list[UsageRecord]:
        with self._lock:
            return list(self._records)

    # ------------------------------------------------------------ reporting

    def usage_summary(self) -> UsageSummary:
        with self._lock:
            recs: Iterable[UsageRecord] = list(self._records)
        by_model: dict[str, int] = {}
        by_provider: dict[str, int] = {}
        total_in = total_out = 0
        total_cost = 0.0
        cache_hits = 0
        count = 0
        for r in recs:
            count += 1
            total_in += r.input_tokens
            total_out += r.output_tokens
            total_cost += 0.0 if r.cache_hit else r.cost
            cache_hits += int(r.cache_hit)
            by_model[r.model] = by_model.get(r.model, 0) + 1
            by_provider[r.provider] = by_provider.get(r.provider, 0) + 1
        return UsageSummary(
            total_requests=count,
            total_input_tokens=total_in,
            total_output_tokens=total_out,
            total_cost=round(total_cost, 6),
            cache_hits=cache_hits,
            by_model=by_model,
            by_provider=by_provider,
        )

    def savings_report(self) -> SavingsReport:
        with self._lock:
            recs = list(self._records)
            saved_cache = self._saved_from_cache_usd
            saved_routing = self._saved_from_routing_usd
        spend = sum(r.cost for r in recs if not r.cache_hit)
        return SavingsReport(
            total_requests=len(recs),
            cache_hits=sum(1 for r in recs if r.cache_hit),
            routed_to_cheap=sum(1 for r in recs if r.routed_to_cheap and not r.cache_hit),
            routed_to_local=sum(1 for r in recs if r.routed_to_local and not r.cache_hit),
            total_spend_usd=round(spend, 6),
            saved_from_cache_usd=round(saved_cache, 6),
            saved_from_routing_usd=round(saved_routing, 6),
            total_savings_usd=round(saved_cache + saved_routing, 6),
        )
