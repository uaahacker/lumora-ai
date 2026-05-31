# FAQ

### Why another LLM wrapper?
Most wrappers are SDK-style. LumoraAI is a **gateway** — it adds routing,
caching, cost control, and a savings report on top of any OpenAI-compatible
or Ollama endpoint, with one consistent API.

### Does LumoraAI store my API keys?
No. Keys are read from env vars or passed in code and used only in the
`Authorization` header. They are never written to the cache, logs, or
errors (errors are passed through `redact_secrets`).

### Is the cache safe to share across machines?
The SQLite file contains model outputs and normalized prompts. Treat it as
user-visible data. It is not encrypted at rest. For shared deployments,
plug in a custom `BaseCache` backend.

### Why no `tiktoken` dependency?
To keep install small and friction-free for MVP. Token counts are estimated
with a `len(text) / 4` heuristic. When the provider returns real `usage`,
that wins. You can swap in a more accurate counter later without changing
the public API.

### Why doesn't LumoraAI rotate API keys?
Because that is the standard pattern abusers use to dodge rate limits.
Enterprise users will get a controlled `key_pool` for legitimate failover
(field already exists in `ProviderConfig`).

### How accurate is the savings report?
- **Cache savings** are exact for the model the router originally picked.
- **Routing savings** are approximate (smart-tier minus actual). They are a
  reasonable upper bound for "money you didn't spend by downshifting."

### Can I use Anthropic directly?
Today, route via OpenRouter (`anthropic/claude-3.5-sonnet`). A native
`AnthropicProvider` is on the roadmap; `BaseProvider` is designed for it.

### Will there be async support?
Yes — planned for 0.2.0 alongside the Anthropic adapter.

### Where will the SaaS dashboard live?
A separate repo. The Python library will stay open-source under Apache-2.0
and the public API will not break.
