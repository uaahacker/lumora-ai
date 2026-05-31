# LumoraAI

> **Make every model smarter, cheaper, and easier to control.**

LumoraAI is an open-source Python library that sits between your application and any LLM provider. It improves prompt quality, routes requests to the right model, caches repeated answers, tracks cost, handles rate limits, and helps developers get better results from cheaper or local models.

- Package name (PyPI): `lumora-ai`
- Import name: `lumora`
- License: Apache-2.0

---

## Why LumoraAI?

Building real apps on top of LLMs hits the same wall every time:

- **AI bills are unpredictable.** A small prompt loop can quietly burn a budget overnight.
- **Prompts are weak.** Small or local models underperform because users send vague prompts.
- **Local models are powerful but inconsistent.** They need structure.
- **Rate limits are everywhere.** Every provider returns 429s at the worst moment.
- **Switching providers is painful.** OpenAI, OpenRouter, Ollama, vLLM, LM Studio all have slightly different SDKs.

LumoraAI gives you one client, one config, and one mental model.

---

## What it gives you

- **Unified `LumoraClient.chat()`** that works with OpenAI, OpenRouter, Ollama, vLLM, LM Studio, Together-like, or any OpenAI-compatible endpoint.
- **Smart model router** that picks `cheap`, `balanced`, or `smart` based on the prompt.
- **SQLite cache** with optional fuzzy matching (Redis backend is planned).
- **Rule-based prompt enhancer** that improves vague prompts *without* calling another expensive model.
- **Cost tracker + budget guard** with editable per-model pricing.
- **Retry/backoff** for `429/5xx` (no shady key rotation).
- **Savings report** that estimates money saved from cache hits and from routing to cheaper/local models.
- **CLI** built with Typer + Rich.

---

## Install

```bash
pip install lumora-ai
```

Or, from source (recommended while iterating):

```bash
git clone <this-repo>
cd lumora-ai
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Quick start

```python
from lumora import LumoraClient

client = LumoraClient(
    providers=[
        {
            "name": "openrouter",
            "type": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "YOUR_KEY",
            "models": {
                "cheap":    "openai/gpt-4o-mini",
                "balanced": "openai/gpt-4o",
                "smart":    "anthropic/claude-3.5-sonnet",
            },
        }
    ],
    cache_enabled=True,
    budget_limit_usd=5.00,
)

response = client.chat(
    messages=[{"role": "user", "content": "Write a professional email asking for payment."}],
    quality="balanced",
)

print(response.content)
print(response.model_used)
print(response.estimated_cost)
print(response.cache_hit)
```

---

## Ollama (local) example

```python
from lumora import LumoraClient

client = LumoraClient(providers=[{
    "name": "local",
    "type": "ollama",
    "base_url": "http://localhost:11434",
    "models": {"cheap": "ollama/llama3.1", "balanced": "ollama/llama3.1"},
}])

print(client.chat(messages=[{"role": "user", "content": "3 hike ideas"}]).content)
```

---

## Prompt enhancement example

```python
from lumora.enhancement import PromptEnhancer

result = PromptEnhancer().enhance("write email payment")
print(result.changed)            # True
print(result.enhanced_prompt)    # structured, polite, with subject + body
```

LumoraAI **does not** rewrite code, legal, or medical prompts, and it leaves already-detailed prompts alone.

---

## Caching example

```python
client.chat(messages=[{"role": "user", "content": "same prompt"}])
again = client.chat(messages=[{"role": "user", "content": "same prompt"}])
assert again.cache_hit is True
```

Enable fuzzy matching for *similar* prompts:

```python
client = LumoraClient(providers=[...], cache_fuzzy=True, cache_similarity_threshold=0.92)
```

---

## Cost tracking & savings

```python
print(client.usage_summary())
print(client.savings_report())
```

`savings_report()` estimates:

- how many calls were served from cache,
- approximate USD saved by serving from cache,
- approximate USD saved by routing simple prompts to cheap/local models,
- total estimated spend and total estimated savings.

---

## CLI usage

```bash
lumora init                 # creates .lumora.toml in the current folder
lumora chat "Summarize the OWASP top 10"
lumora cache stats
lumora cache clear
lumora usage                # nice Rich tables for usage + savings
```

The init command produces a config like:

```toml
[default]
cache_enabled = true
budget_limit_usd = 5.0

[[providers]]
name = "openrouter"
type = "openai_compatible"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"

[providers.models]
cheap = "openai/gpt-4o-mini"
balanced = "openai/gpt-4o"
smart = "anthropic/claude-3.5-sonnet"
```

---

## Roadmap

- **Phase 1 — Python library (this repo).** Routing, cache, enhancer, cost, CLI.
- **Phase 2 — Paid SaaS dashboard.** Hosted analytics, team usage, prompt libraries.
- **Phase 3 — Enterprise self-hosted gateway.** SSO, audit logs, key vaults, on-prem deploy, controlled key pools.

The current code is intentionally structured so the SaaS dashboard and enterprise gateway can be added as separate packages without changing the public Python API.

---

## Security notes

- API keys are read from environment variables or passed explicitly; they are **never written to the cache or logs**.
- Error messages are passed through a redactor that strips obvious key/token patterns.
- Prompt logging is **off by default** (`allow_prompt_logging=False`).
- LumoraAI does **not** rotate API keys to bypass provider rate limits. Enterprise users can configure controlled `key_pool` failover in the future.
- Retries respect `429/5xx` only and use exponential backoff with jitter.

---

## Contributing

PRs and issues are welcome. Suggested workflow:

```bash
pip install -e ".[dev]"
pytest
ruff check lumora tests
```

When adding a new provider:

1. Subclass `lumora.providers.BaseProvider`.
2. Register it in `lumora.providers.build_provider`.
3. Add a test that uses an injected mock provider — do not hit the network in CI.

---

## License

Apache-2.0. See [LICENSE](LICENSE).
