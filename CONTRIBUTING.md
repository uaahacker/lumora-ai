# Contributing to LumoraAI

Thanks for your interest! LumoraAI is an open-source project and contributions are welcome.

## Development setup

```bash
git clone https://github.com/lumora-ai/lumora-ai
cd lumora-ai
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
pytest -q
```

## Coding standards

- Python 3.10+, full type hints, `pydantic` models for config and responses.
- Keep public APIs small and stable; prefer adding new modules over breaking existing ones.
- Never log prompts unless `allow_prompt_logging=True`. Never write API keys to cache, logs, or error messages.
- All HTTP calls go through `httpx`. No global mutable state outside `LumoraClient`.

## Adding a new provider

1. Subclass `lumora.providers.BaseProvider` and implement `chat(...)`.
2. Register it in `lumora.providers.build_provider`.
3. Add a unit test that uses a mock subclass — do not hit the network in CI.

## Adding a new cache backend

1. Subclass `lumora.cache.BaseCache`.
2. Pass an instance into `LumoraClient(cache_backend=...)`.
3. Add a unit test that covers `put / get_exact / get_fuzzy / clear / stats`.

## Pull requests

- One focused change per PR.
- Include or update tests.
- Run `pytest -q` and (optionally) `ruff check lumora tests` before pushing.

## Security

Please do not file security issues in the public tracker. Email the maintainer
listed in `pyproject.toml` instead, or open a private advisory on GitHub.
