# LumoraAI Documentation

Welcome. This folder contains the long-form documentation for **LumoraAI**.
For a quick overview, see the top-level [README.md](../README.md).

## Contents

- [Getting Started](getting-started.md) — install, configure, first call.
- [Providers](providers.md) — OpenRouter, OpenAI, Ollama, vLLM, LM Studio, custom endpoints.
- [Routing](routing.md) — how `cheap` / `balanced` / `smart` is decided.
- [Caching](caching.md) — exact and fuzzy SQLite cache.
- [Prompt Enhancement](prompt-enhancement.md) — rule-based, safe-by-default.
- [Cost & Savings](cost.md) — pricing, budget guard, savings report.
- [CLI](cli.md) — `lumora init | chat | cache | usage`.
- [Security](security.md) — what LumoraAI will and will not do.
- [Publishing to PyPI](publishing.md) — for maintainers.
- [FAQ](faq.md)

## Roadmap

- **Phase 1 — Python library (this repo).**
- **Phase 2 — Hosted SaaS dashboard.** Team analytics, prompt libraries.
- **Phase 3 — Enterprise self-hosted gateway.** SSO, audit logs, key vaults.

The public Python API will stay stable across these phases.
