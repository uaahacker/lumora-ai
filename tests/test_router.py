from lumora.config import ProviderConfig
from lumora.models import Message
from lumora.routing import ModelRouter


def _providers():
    return [
        ProviderConfig(
            name="openrouter",
            type="openai_compatible",
            base_url="https://openrouter.ai/api/v1",
            api_key="x",
            models={"cheap": "openai/gpt-4o-mini", "balanced": "openai/gpt-4o", "smart": "anthropic/claude-3.5-sonnet"},
        ),
        ProviderConfig(
            name="local",
            type="ollama",
            base_url="http://localhost:11434",
            models={"cheap": "ollama/llama3.1"},
        ),
    ]


def test_simple_prompt_routes_cheap_and_prefers_local():
    r = ModelRouter(_providers())
    decision = r.route([Message(role="user", content="hi")])
    assert decision.quality == "cheap"
    assert decision.routed_to_cheap is True
    assert decision.routed_to_local is True
    assert decision.provider == "local"


def test_complex_prompt_routes_smart():
    r = ModelRouter(_providers())
    decision = r.route([Message(role="user", content="design a distributed kubernetes architecture with concurrency considerations")])
    assert decision.quality == "smart"
    assert decision.provider == "openrouter"


def test_explicit_model_respected():
    r = ModelRouter(_providers())
    decision = r.route([Message(role="user", content="x")], explicit_model="openai/gpt-4o")
    assert decision.model == "openai/gpt-4o"


def test_budget_pressure_downshifts():
    r = ModelRouter(_providers(), budget_limit_usd=1.0)
    decision = r.route(
        [Message(role="user", content="please write a normal balanced length business note that is just regular")],
        current_spend_usd=0.95,
    )
    assert decision.quality == "cheap"
