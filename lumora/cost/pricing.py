"""Approximate, editable per-model pricing in USD per 1K tokens.

These numbers are intentionally rough. Override DEFAULT_PRICING at runtime
to keep costs in sync with your provider's current rates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    input_per_1k: float   # USD per 1,000 input tokens
    output_per_1k: float  # USD per 1,000 output tokens

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            (input_tokens / 1000.0) * self.input_per_1k
            + (output_tokens / 1000.0) * self.output_per_1k
        )


# Approximate pricing. Edit freely.
DEFAULT_PRICING: dict[str, ModelPricing] = {
    # OpenAI-style
    "openai/gpt-4o-mini":        ModelPricing(0.00015, 0.00060),
    "openai/gpt-4o":             ModelPricing(0.00250, 0.01000),
    "gpt-4o-mini":               ModelPricing(0.00015, 0.00060),
    "gpt-4o":                    ModelPricing(0.00250, 0.01000),
    "gpt-4.1-mini":              ModelPricing(0.00040, 0.00160),

    # Anthropic-style (via OpenRouter or others)
    "anthropic/claude-3.5-sonnet": ModelPricing(0.00300, 0.01500),
    "anthropic/claude-3-haiku":    ModelPricing(0.00025, 0.00125),

    # Common open-source via OpenRouter
    "meta-llama/llama-3.1-70b-instruct": ModelPricing(0.00080, 0.00080),
    "meta-llama/llama-3.1-8b-instruct":  ModelPricing(0.00020, 0.00020),

    # Local models are free at inference time.
    "ollama/llama3.1":  ModelPricing(0.0, 0.0),
    "ollama/llama3":    ModelPricing(0.0, 0.0),
    "ollama/qwen2.5":   ModelPricing(0.0, 0.0),
    "ollama/mistral":   ModelPricing(0.0, 0.0),
}

# Conservative default for unknown models so we don't silently underestimate.
UNKNOWN_PRICING = ModelPricing(0.00100, 0.00300)


def get_pricing(model: str, overrides: dict[str, ModelPricing] | None = None) -> ModelPricing:
    """Look up pricing for a model. Falls back to UNKNOWN_PRICING."""
    if overrides and model in overrides:
        return overrides[model]
    if model in DEFAULT_PRICING:
        return DEFAULT_PRICING[model]
    # Try stripping a provider prefix like 'openrouter/'.
    if "/" in model:
        tail = model.split("/", 1)[1]
        if tail in DEFAULT_PRICING:
            return DEFAULT_PRICING[tail]
    # Ollama / local heuristic.
    if model.startswith("ollama/") or model.startswith("local/"):
        return ModelPricing(0.0, 0.0)
    return UNKNOWN_PRICING


def estimate_tokens(text: str) -> int:
    """Rough token count without tiktoken: ~4 characters per token."""
    if not text:
        return 0
    # Slight over-estimate for safety in budget checks.
    return max(1, int(len(text) / 4) + 1)
