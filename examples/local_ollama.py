"""Local Ollama usage example.

Requires Ollama running locally:  https://ollama.com
  ollama pull llama3.1
  ollama serve   # (usually starts automatically)
"""

from __future__ import annotations

from lumora import LumoraClient


def main() -> None:
    client = LumoraClient(
        providers=[
            {
                "name": "local",
                "type": "ollama",
                "base_url": "http://localhost:11434",
                "models": {
                    "cheap": "ollama/llama3.1",
                    "balanced": "ollama/llama3.1",
                },
            }
        ],
        cache_enabled=True,
    )

    resp = client.chat(
        messages=[{"role": "user", "content": "Give me 3 ideas for a Sunday hike."}],
        quality="cheap",
    )

    print(resp.content)
    print("---")
    print(f"model_used: {resp.model_used}  provider: {resp.provider_used}")
    print(f"latency_ms: {resp.latency_ms}")


if __name__ == "__main__":
    main()
