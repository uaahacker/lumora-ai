"""End-to-end client tests using a mocked provider (no network)."""

from __future__ import annotations

from lumora.client import LumoraClient
from lumora.config import ProviderConfig
from lumora.models import Message
from lumora.providers.base import BaseProvider, ProviderChatResult


class MockProvider(BaseProvider):
    def __init__(self, config: ProviderConfig, reply: str = "hello from mock"):
        super().__init__(config)
        self.reply = reply
        self.calls = 0

    def chat(self, messages, model, temperature=0.7, max_tokens=None, timeout=None):
        self.calls += 1
        return ProviderChatResult(
            content=self.reply,
            model=model,
            raw={"mock": True},
            input_tokens=20,
            output_tokens=10,
        )


def _make_client(tmp_path, **kwargs):
    cfg = ProviderConfig(
        name="mockp",
        type="openai_compatible",
        base_url="https://mock.test/v1",
        api_key="x",
        models={"cheap": "openai/gpt-4o-mini", "balanced": "openai/gpt-4o", "smart": "anthropic/claude-3.5-sonnet"},
    )
    client = LumoraClient(
        providers=[cfg],
        cache_path=str(tmp_path / "c.sqlite"),
        **kwargs,
    )
    mock = MockProvider(cfg)
    client._providers["mockp"] = mock  # inject mock
    return client, mock


def test_chat_returns_structured_response(tmp_path):
    client, mock = _make_client(tmp_path)
    resp = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert resp.content == "hello from mock"
    assert resp.provider_used == "mockp"
    assert resp.estimated_input_tokens == 20
    assert resp.estimated_output_tokens == 10
    assert resp.cache_hit is False
    assert mock.calls == 1


def test_second_identical_call_is_cache_hit(tmp_path):
    client, mock = _make_client(tmp_path)
    client.chat(messages=[{"role": "user", "content": "same prompt"}])
    resp2 = client.chat(messages=[{"role": "user", "content": "same prompt"}])
    assert resp2.cache_hit is True
    assert mock.calls == 1  # second call hit the cache


def test_savings_report_records_cache_savings(tmp_path):
    client, _ = _make_client(tmp_path)
    client.chat(messages=[{"role": "user", "content": "same prompt"}])
    client.chat(messages=[{"role": "user", "content": "same prompt"}])
    report = client.savings_report()
    assert report.cache_hits == 1
    assert report.saved_from_cache_usd >= 0  # may be 0 for unknown pricing, but field exists


def test_explicit_model_is_respected(tmp_path):
    client, _ = _make_client(tmp_path)
    resp = client.chat(
        messages=[{"role": "user", "content": "hi"}],
        model="openai/gpt-4o",
    )
    assert resp.model_used == "openai/gpt-4o"
