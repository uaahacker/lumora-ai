"""Demonstrates cost savings from caching + routing using a mocked provider.

This runs fully offline so you can see the savings report without spending money.
"""

from __future__ import annotations

from lumora.client import LumoraClient
from lumora.config import ProviderConfig
from lumora.providers.base import BaseProvider, ProviderChatResult


class FakeProvider(BaseProvider):
    def chat(self, messages, model, temperature=0.7, max_tokens=None, timeout=None):
        return ProviderChatResult(
            content=f"[fake reply from {model}]",
            model=model,
            raw={"fake": True},
            input_tokens=500,
            output_tokens=300,
        )


def main() -> None:
    cfg = ProviderConfig(
        name="fake",
        type="openai_compatible",
        base_url="https://fake.local/v1",
        api_key="x",
        models={
            "cheap": "openai/gpt-4o-mini",
            "balanced": "openai/gpt-4o",
            "smart": "anthropic/claude-3.5-sonnet",
        },
    )
    client = LumoraClient(providers=[cfg], cache_path=".demo_cache.sqlite")
    client._providers["fake"] = FakeProvider(cfg)  # inject

    # 1) Short prompt -> routed to cheap.
    client.chat(messages=[{"role": "user", "content": "hi"}])
    # 2) Long complex prompt -> smart model.
    client.chat(messages=[{"role": "user", "content":
        "Design a distributed system with kubernetes, concurrency control, "
        "and a clear threat model. Discuss trade-offs and complexity."}])
    # 3) Repeat of (1) -> cache hit.
    client.chat(messages=[{"role": "user", "content": "hi"}])

    print(client.usage_summary().model_dump_json(indent=2))
    print(client.savings_report().model_dump_json(indent=2))


if __name__ == "__main__":
    main()
