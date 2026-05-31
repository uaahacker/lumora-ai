"""Pydantic models for requests, responses, and reports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Quality = Literal["cheap", "balanced", "smart"]
Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    role: Role
    content: str


class ChatResponse(BaseModel):
    content: str
    model_used: str
    provider_used: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    cache_hit: bool = False
    latency_ms: int = 0
    request_id: str = ""
    raw_response: dict[str, Any] | None = None


class UsageRecord(BaseModel):
    request_id: str
    provider: str
    model: str
    quality: Quality | None = None
    input_tokens: int
    output_tokens: int
    cost: float
    cache_hit: bool = False
    routed_to_cheap: bool = False
    routed_to_local: bool = False


class UsageSummary(BaseModel):
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    cache_hits: int
    by_model: dict[str, int] = Field(default_factory=dict)
    by_provider: dict[str, int] = Field(default_factory=dict)


class SavingsReport(BaseModel):
    total_requests: int
    cache_hits: int
    routed_to_cheap: int
    routed_to_local: int
    total_spend_usd: float
    saved_from_cache_usd: float
    saved_from_routing_usd: float
    total_savings_usd: float

    @property
    def savings_pct(self) -> float:
        denom = self.total_spend_usd + self.total_savings_usd
        if denom <= 0:
            return 0.0
        return round((self.total_savings_usd / denom) * 100, 2)
