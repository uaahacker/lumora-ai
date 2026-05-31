# Routing

The `ModelRouter` picks a `(provider, model, quality)` for every request.

## Quality tiers

| Tier | When chosen | Typical use |
|---|---|---|
| `cheap` | very short prompts, no complex keywords | quick replies, formatting, classification |
| `balanced` | normal-length business prompts | summaries, writing, Q&A |
| `smart` | complex/architecture/code/math/long prompts | reasoning, design, planning |

## Decision flow

1. **Explicit `model=`** wins. The router forwards it as-is and picks the first matching provider.
2. **Explicit `quality=`** is respected if set.
3. Otherwise the router classifies the prompt:
   - Contains code fences, function/class signatures, math symbols → `smart`.
   - Contains keywords like `architecture`, `refactor`, `algorithm`, `security`, `threat model`, `kubernetes`, `concurrency`, `step by step`, `plan` → `smart`.
   - Combined user/system text > 1200 chars → `smart`.
   - Combined text < 160 chars → `cheap`.
   - Otherwise → `balanced`.
4. **Budget pressure**: if `current_spend ≥ 0.85 × budget_limit_usd`, downshift any non-cheap request to `cheap`.
5. **Local preference**: if the chosen tier is `cheap` *and* an Ollama provider is configured, prefer the local model.
6. **Fallback**: if no provider has the chosen tier, fall back through `balanced → smart → cheap`.

## Inspecting decisions

```python
from lumora.routing import ModelRouter
from lumora.models import Message

decision = client.router.route(
    messages=[Message(role="user", content="hi")],
    current_spend_usd=client.cost_tracker.total_spend,
)
print(decision.provider, decision.model, decision.quality, decision.reason)
```

`RouteDecision` also exposes `routed_to_cheap` and `routed_to_local`, which feed the savings report.

## Tuning

For now, routing is heuristic and intentionally simple — no extra model call.
A learned/ML router is on the roadmap, but only as an opt-in module.
