import pytest

from lumora.cost import CostTracker
from lumora.exceptions import BudgetExceededError
from lumora.models import UsageRecord


def test_budget_blocks_when_exceeded():
    t = CostTracker(budget_limit_usd=0.0001)
    with pytest.raises(BudgetExceededError):
        t.check_budget(1.0)


def test_savings_from_cache_uses_reference_model():
    t = CostTracker()
    t.record(
        UsageRecord(
            request_id="r1", provider="openrouter", model="openai/gpt-4o",
            input_tokens=1000, output_tokens=500, cost=0.0, cache_hit=True,
        ),
        reference_model_for_savings="openai/gpt-4o",
    )
    report = t.savings_report()
    assert report.cache_hits == 1
    assert report.saved_from_cache_usd > 0


def test_savings_from_routing_when_downshifted():
    t = CostTracker()
    t.record(
        UsageRecord(
            request_id="r2", provider="openrouter", model="openai/gpt-4o-mini",
            input_tokens=1000, output_tokens=500, cost=0.0,
            routed_to_cheap=True,
        ),
        reference_model_for_savings="openai/gpt-4o",
    )
    report = t.savings_report()
    assert report.saved_from_routing_usd > 0
    assert report.routed_to_cheap == 1


def test_usage_summary_counts_records():
    t = CostTracker()
    for i in range(3):
        t.record(UsageRecord(
            request_id=f"r{i}", provider="p", model="m",
            input_tokens=10, output_tokens=20, cost=0.001,
        ))
    summary = t.usage_summary()
    assert summary.total_requests == 3
    assert summary.total_input_tokens == 30
    assert summary.by_model.get("m") == 3
