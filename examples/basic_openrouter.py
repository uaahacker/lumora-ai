"""Basic OpenRouter usage example.

Requires:
  pip install -e .
  setx OPENROUTER_API_KEY "sk-or-..."   # Windows
  export OPENROUTER_API_KEY="sk-or-..." # macOS/Linux
"""

from __future__ import annotations

import os

from lumora import LumoraClient


def main() -> None:
    client = LumoraClient(
        providers=[
            {
                "name": "openrouter",
                "type": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": os.environ.get("OPENROUTER_API_KEY"),
                "models": {
                    "cheap": "openai/gpt-4o-mini",
                    "balanced": "openai/gpt-4o",
                    "smart": "anthropic/claude-3.5-sonnet",
                },
            }
        ],
        cache_enabled=True,
        budget_limit_usd=5.00,
    )

    resp = client.chat(
        messages=[
            {"role": "user", "content": "Write a professional email to a client asking for payment."}
        ],
        quality="balanced",
    )

    print("---")
    print(resp.content)
    print("---")
    print(f"model_used    : {resp.model_used}")
    print(f"provider_used : {resp.provider_used}")
    print(f"cache_hit     : {resp.cache_hit}")
    print(f"estimated_cost: ${resp.estimated_cost:.6f}")
    print(f"latency_ms    : {resp.latency_ms}")


if __name__ == "__main__":
    main()
