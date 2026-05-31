"""Exponential-backoff retry helper.

We do NOT rotate API keys. That is an abuse pattern. Enterprise users can
configure an opt-in `key_pool` on a provider for legitimate failover only.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from lumora.exceptions import ProviderError, RateLimitError


T = TypeVar("T")

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 10.0
    jitter: float = 0.25


def with_retries(fn: Callable[[], T], policy: RetryPolicy | None = None) -> T:
    """Run `fn` with exponential backoff on retryable provider errors."""
    pol = policy or RetryPolicy()
    last_exc: Exception | None = None

    for attempt in range(pol.max_retries + 1):
        try:
            return fn()
        except ProviderError as e:
            last_exc = e
            if e.status_code not in RETRYABLE_STATUS or attempt >= pol.max_retries:
                if e.status_code == 429:
                    raise RateLimitError(str(e), status_code=429) from e
                raise
            delay = min(pol.max_delay, pol.base_delay * (2 ** attempt))
            delay += random.uniform(0, pol.jitter)
            time.sleep(delay)

    assert last_exc is not None  # pragma: no cover
    raise last_exc
