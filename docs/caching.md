# Caching

LumoraAI ships a SQLite cache. The interface (`BaseCache`) is generic so a Redis or
Postgres backend can be added later without changing `LumoraClient`.

## How keys are built

1. Messages are **normalized** (lowercased, whitespace-collapsed, role-prefixed).
2. The normalized string + model name are hashed with SHA-256.
3. The key is looked up first by exact match, then optionally by fuzzy match.

API keys, tokens, and obvious secret-like metadata fields are **stripped before write**.

## Exact cache (default)

```python
client = LumoraClient(providers=[...], cache_enabled=True)

client.chat(messages=[{"role": "user", "content": "same prompt"}])
again = client.chat(messages=[{"role": "user", "content": "same prompt"}])
assert again.cache_hit is True
assert again.estimated_cost == 0.0
```

## Fuzzy cache (opt-in)

For *similar* prompts, enable fuzzy matching. It uses Python's `difflib.SequenceMatcher`
across the last 500 entries.

```python
client = LumoraClient(
    providers=[...],
    cache_enabled=True,
    cache_fuzzy=True,
    cache_similarity_threshold=0.92,   # 0.0 (always) .. 1.0 (exact only)
)
```

Trade-offs:
- Higher threshold → fewer false matches, fewer cache hits.
- Lower threshold → more reuse, but risk of returning a stale-looking answer.

## Disabling per call

```python
client.chat(messages=[...], use_cache=False)
```

## Stats and clearing

```python
print(client.cache.stats())
deleted = client.cache.clear()
```

Or via CLI:

```bash
lumora cache stats
lumora cache clear
```

## Custom backend

Pass any subclass of `lumora.cache.BaseCache` to `LumoraClient(cache_backend=...)`.

```python
from lumora.cache import BaseCache

class MyRedisCache(BaseCache):
    def get_exact(self, key): ...
    def get_fuzzy(self, normalized_prompt, threshold): ...
    def put(self, entry): ...
    def clear(self) -> int: ...
    def stats(self) -> dict: ...
```
