# Getting Started

## Install

```bash
pip install lumora-ai
```

Or from source:

```bash
git clone https://github.com/lumora-ai/lumora-ai
cd lumora-ai
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -e ".[dev]"
```

Python 3.10+ is required.

## Set your API key

LumoraAI never stores keys. Pass one in code, or use an environment variable.

```powershell
# Windows PowerShell (current session)
$env:OPENROUTER_API_KEY = "sk-or-..."

# Windows persistent
setx OPENROUTER_API_KEY "sk-or-..."   # reopen the shell

# macOS / Linux
export OPENROUTER_API_KEY="sk-or-..."
```

## First call

```python
import os
from lumora import LumoraClient

client = LumoraClient(
    providers=[{
        "name": "openrouter",
        "type": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ["OPENROUTER_API_KEY"],
        "models": {
            "cheap":    "openai/gpt-4o-mini",
            "balanced": "openai/gpt-4o",
            "smart":    "anthropic/claude-3.5-sonnet",
        },
    }],
    cache_enabled=True,
    budget_limit_usd=5.00,
)

resp = client.chat(
    messages=[{"role": "user", "content": "Hello in one sentence."}],
    quality="cheap",
    max_tokens=80,   # keep small while testing
)
print(resp.content)
print(resp.model_used, resp.cache_hit, f"${resp.estimated_cost:.6f}")
```

## Response object

`client.chat(...)` returns a `ChatResponse` with:

| Field | Description |
|---|---|
| `content` | The assistant's reply text. |
| `model_used` | Model the request was actually sent to. |
| `provider_used` | Provider name from your config. |
| `estimated_input_tokens` | Tokens in (provider value if available, else ~4 char/token estimate). |
| `estimated_output_tokens` | Tokens out, same rule. |
| `estimated_cost` | USD, from `lumora.cost.pricing`. |
| `cache_hit` | `True` if served from cache. |
| `latency_ms` | Wall-clock latency. |
| `request_id` | Short ID used in logs. |
| `raw_response` | Raw provider JSON (for debugging). |

## Next steps

- [Providers](providers.md) — add Ollama or a custom OpenAI-compatible endpoint.
- [Routing](routing.md) — let LumoraAI pick the model for you.
- [Cost & Savings](cost.md) — set a budget and read the savings report.
