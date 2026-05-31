# Security

LumoraAI is a thin layer in front of your model providers. The guardrails here
are intentional and conservative.

## What LumoraAI does

- Reads API keys from environment variables or from a config object you pass in.
- Sends them **only** in the `Authorization: Bearer <key>` header to the provider.
- Stores responses (not keys) in the local SQLite cache.
- Strips obvious secret patterns (`sk-...`, `Bearer ...`, `api_key=...`) from error messages via `redact_secrets()`.
- Drops cache-metadata keys whose name contains `key`, `token`, or `secret`.
- Retries only on `429 / 500 / 502 / 503 / 504` with exponential backoff + jitter.

## What LumoraAI will NOT do

- It will **not** rotate API keys to bypass a provider's rate limits. That is an
  abuse pattern and is explicitly out of scope. Enterprise users can configure
  a controlled `key_pool` for legitimate failover in the future (field exists,
  not enforced in MVP).
- It will **not** log prompts by default. Set `allow_prompt_logging=True`
  explicitly if you want to opt in for your own debugging.
- It will **not** persist API keys or `Authorization` headers to disk.

## Recommendations

- Keep keys in environment variables or a secret manager. Avoid hard-coding
  them in `.lumora.toml` (use `api_key_env` instead).
- Add `.lumora.toml`, `*.sqlite`, and `.env*` to your `.gitignore` (already done
  in this repo's template).
- For multi-tenant servers, instantiate one `LumoraClient` per tenant so that
  the cache and `CostTracker` are properly isolated.
- Treat the cache file as containing model output for your users; it is **not**
  encrypted at rest. Put it on encrypted storage if your data classification
  requires it.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems. Use
GitHub's private security advisory feature on this repo, or email the
maintainer listed in `pyproject.toml`.
