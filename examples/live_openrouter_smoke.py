"""Live OpenRouter smoke test that fits inside a small free-credit budget.

Run:
  setx OPENROUTER_API_KEY "sk-or-..."   # Windows (reopen shell)
  $env:OPENROUTER_API_KEY = "..."        # PowerShell (current shell)
  python examples/live_openrouter_smoke.py
"""

from __future__ import annotations

import os

from lumora import LumoraClient


def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("Set OPENROUTER_API_KEY first.")

    client = LumoraClient(
        providers=[
            {
                "name": "openrouter",
                "type": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": key,
                "models": {
                    "cheap":    "openai/gpt-4o-mini",
                    "balanced": "openai/gpt-4o-mini",
                    "smart":    "openai/gpt-4o-mini",
                },
            }
        ],
        cache_enabled=True,
        budget_limit_usd=1.00,
    )

    # 1) First call: short prompt, capped to fit a free-tier credit window.
    print("--- Call 1: live request ---")
    r1 = client.chat(
        messages=[{"role": "user", "content": "In one sentence, what is LumoraAI?"}],
        quality="cheap",
        max_tokens=80,
    )
    print(r1.content)
    print(f"model={r1.model_used} cache_hit={r1.cache_hit} "
          f"cost=${r1.estimated_cost:.6f} latency={r1.latency_ms}ms")

    # 2) Same prompt: should be a cache hit (no network).
    print("--- Call 2: should be cache hit ---")
    r2 = client.chat(
        messages=[{"role": "user", "content": "In one sentence, what is LumoraAI?"}],
        quality="cheap",
        max_tokens=80,
    )
    print(f"cache_hit={r2.cache_hit} latency={r2.latency_ms}ms")

    # 3) Reports
    print("--- Usage summary ---")
    print(client.usage_summary().model_dump_json(indent=2))
    print("--- Savings report ---")
    print(client.savings_report().model_dump_json(indent=2))


if __name__ == "__main__":
    main()
