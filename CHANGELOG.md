# Changelog

All notable changes to LumoraAI are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-05-31

### Added
- Initial MVP release of `lumora-ai`.
- `LumoraClient` with unified `.chat()` method.
- Provider adapters: `OpenAICompatibleProvider` (OpenRouter, OpenAI, vLLM, LM Studio, Together-like), `OllamaProvider`.
- Heuristic `ModelRouter` with `cheap` / `balanced` / `smart` tiers, local-model preference, and budget-pressure downshift.
- `SQLiteCache` with optional `difflib` fuzzy matching; pluggable `BaseCache` interface for future Redis backend.
- Rule-based `PromptEnhancer` that skips code, legal, medical, and already-detailed prompts.
- `CostTracker` with editable per-model pricing, budget guard, usage summary, and savings report.
- Exponential-backoff retry on 429/5xx (no API key rotation).
- Structured local logging with per-request IDs; prompt logging disabled by default.
- Typer + Rich CLI: `lumora init | chat | cache stats | cache clear | usage`.
- 21 unit tests and 4 example scripts.
