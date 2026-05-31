"""Configuration models and loaders for LumoraAI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from lumora.exceptions import ConfigurationError

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


ProviderType = Literal["openai_compatible", "ollama"]


class ProviderConfig(BaseModel):
    name: str
    type: ProviderType
    base_url: str
    api_key: str | None = None
    api_key_env: str | None = None
    models: dict[str, str] = Field(default_factory=dict)
    # Reserved for enterprise: controlled, opt-in key pools. Not used in MVP.
    key_pool: list[str] | None = None
    timeout: float = 60.0
    extra_headers: dict[str, str] = Field(default_factory=dict)

    @field_validator("models")
    @classmethod
    def _models_lower(cls, v: dict[str, str]) -> dict[str, str]:
        return {k.lower(): val for k, val in v.items()}

    def resolved_api_key(self) -> str | None:
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None


class LumoraConfig(BaseModel):
    providers: list[ProviderConfig]
    cache_enabled: bool = True
    cache_path: str = ".lumora_cache.sqlite"
    cache_similarity_threshold: float = 0.92
    cache_fuzzy: bool = False
    budget_limit_usd: float | None = None
    enhance_prompt_default: bool = False
    allow_prompt_logging: bool = False
    max_retries: int = 3
    request_timeout: float = 60.0

    @field_validator("providers")
    @classmethod
    def _need_providers(cls, v: list[ProviderConfig]) -> list[ProviderConfig]:
        if not v:
            raise ValueError("At least one provider must be configured.")
        return v


def load_config_from_toml(path: str | Path) -> LumoraConfig:
    """Load a LumoraConfig from a .lumora.toml file."""
    p = Path(path)
    if not p.exists():
        raise ConfigurationError(f"Config file not found: {p}")
    with p.open("rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    default = data.get("default", {})
    providers_raw = data.get("providers", [])
    if not isinstance(providers_raw, list):
        raise ConfigurationError("`providers` must be a TOML array of tables.")

    providers = [ProviderConfig(**p) for p in providers_raw]
    return LumoraConfig(providers=providers, **default)


DEFAULT_TOML_TEMPLATE = """\
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
cheap = "openai/gpt-4o-mini"
balanced = "openai/gpt-4o"
smart = "anthropic/claude-3.5-sonnet"
"""
