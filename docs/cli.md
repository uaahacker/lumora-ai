# CLI

LumoraAI installs a `lumora` command (built on Typer + Rich).

```text
lumora init                       # write .lumora.toml in the current folder
lumora chat "your prompt here"    # one-off chat
lumora cache stats                # show cache backend stats
lumora cache clear                # delete all cached entries
lumora usage                      # Rich tables for usage + savings
```

## `lumora init`

Creates a starter `.lumora.toml` in the current directory:

```toml
[default]
cache_enabled = true
budget_limit_usd = 5.0
enhance_prompt_default = false
allow_prompt_logging = false

[[providers]]
name = "openrouter"
type = "openai_compatible"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"

[providers.models]
cheap    = "openai/gpt-4o-mini"
balanced = "openai/gpt-4o"
smart    = "anthropic/claude-3.5-sonnet"
```

Use `--force` to overwrite.

## `lumora chat`

```bash
lumora chat "Summarize the OWASP top 10" --quality balanced
lumora chat "write email payment" --enhance
lumora chat "explain transformers" --model openai/gpt-4o-mini --no-cache
```

Flags:
- `--quality / -q` : `cheap | balanced | smart` (default `balanced`)
- `--model / -m`   : override the model entirely
- `--enhance`      : run the prompt enhancer
- `--no-cache`     : skip cache for this call

## `lumora cache stats | clear`

```bash
lumora cache stats
lumora cache clear
```

## `lumora usage`

Prints two Rich tables: a usage summary and a savings report.

> Note: usage is tracked **per process**. A fresh `lumora usage` shell will
> show zeros. In a long-running app, use `client.savings_report()` from code.
> Cross-session persistent analytics will land with the SaaS dashboard.
