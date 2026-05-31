# Cost & Savings

LumoraAI estimates spend locally so you can budget without leaving your process.

## Pricing

Pricing lives in `lumora.cost.pricing.DEFAULT_PRICING` as a plain dict
of `model_id -> ModelPricing(input_per_1k, output_per_1k)`.

```python
from lumora.cost import ModelPricing, DEFAULT_PRICING

DEFAULT_PRICING["my-provider/my-model"] = ModelPricing(0.0005, 0.0015)
```

Or pass overrides at construction time:

```python
client = LumoraClient(
    providers=[...],
    pricing_overrides={"openai/gpt-4o-mini": ModelPricing(0.00015, 0.00060)},
)
```

Unknown models fall back to a conservative default
(`ModelPricing(0.001, 0.003)`) so you never silently under-budget.

## Token estimation

For MVP we use a `len(text) / 4` heuristic with a small safety margin.
When the provider returns real `usage`, LumoraAI uses that instead.
No `tiktoken` dependency is required.

## Budget guard

```python
client = LumoraClient(providers=[...], budget_limit_usd=5.00)
```

Before each request, the projected cost is added to the running spend.
If the total would exceed the limit, `BudgetExceededError` is raised
**before** any HTTP call is made.

The router also downshifts to `cheap` when spend reaches 85% of the limit.

## Usage summary

```python
print(client.usage_summary())
# UsageSummary(total_requests=2, cache_hits=1, total_cost=0.000015, ...)
```

## Savings report

```python
print(client.savings_report())
# SavingsReport(
#   total_requests=2,
#   cache_hits=1,
#   routed_to_cheap=1,
#   routed_to_local=0,
#   total_spend_usd=0.000015,
#   saved_from_cache_usd=0.000022,
#   saved_from_routing_usd=0.0,
#   total_savings_usd=0.000022,
# )
```

How savings are computed:

- **`saved_from_cache_usd`** = what the request *would* have cost at the model
  the router originally picked, summed over cache hits.
- **`saved_from_routing_usd`** = (smart-tier cost − actual cost) when LumoraAI
  downshifts a request to a cheaper or local model.

Reports are in-process. For long-running services, log or persist
`UsageRecord`s from `client.cost_tracker.records()`.
