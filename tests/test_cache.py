import os
import tempfile

from lumora.cache import SQLiteCache
from lumora.cache.base import CacheEntry, hash_key, normalize_messages
from lumora.models import Message


def _tmp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return path


def test_exact_cache_round_trip():
    path = _tmp_db()
    try:
        c = SQLiteCache(path)
        msgs = [Message(role="user", content="hello world")]
        norm = normalize_messages(msgs)
        key = hash_key(norm, "openai/gpt-4o-mini")
        c.put(CacheEntry(
            key=key, normalized_prompt=norm, response_content="hi!",
            model="openai/gpt-4o-mini", provider="openrouter",
            created_at=SQLiteCache.now(), metadata={"k": "v"},
        ))
        hit = c.get_exact(key)
        assert hit is not None
        assert hit.response_content == "hi!"
        c.close()
    finally:
        os.unlink(path)


def test_fuzzy_cache_matches_close_prompt():
    path = _tmp_db()
    try:
        c = SQLiteCache(path)
        msgs1 = [Message(role="user", content="please write a polite payment follow up email to a client")]
        norm1 = normalize_messages(msgs1)
        c.put(CacheEntry(
            key=hash_key(norm1, "m"), normalized_prompt=norm1, response_content="cached!",
            model="m", provider="p", created_at=SQLiteCache.now(), metadata={},
        ))
        msgs2 = [Message(role="user", content="please write a polite payment follow up email to the client")]
        hit = c.get_fuzzy(normalize_messages(msgs2), threshold=0.9)
        assert hit is not None
        assert hit.response_content == "cached!"
        c.close()
    finally:
        os.unlink(path)


def test_clear_returns_count():
    path = _tmp_db()
    try:
        c = SQLiteCache(path)
        c.put(CacheEntry(
            key="k", normalized_prompt="n", response_content="r",
            model="m", provider="p", created_at=SQLiteCache.now(), metadata={},
        ))
        assert c.clear() == 1
        c.close()
    finally:
        os.unlink(path)


def test_metadata_strips_secret_like_keys():
    path = _tmp_db()
    try:
        c = SQLiteCache(path)
        c.put(CacheEntry(
            key="k2", normalized_prompt="n", response_content="r",
            model="m", provider="p", created_at=SQLiteCache.now(),
            metadata={"api_key": "sk-abc", "user": "x"},
        ))
        hit = c.get_exact("k2")
        assert hit is not None
        assert "api_key" not in hit.metadata
        assert hit.metadata.get("user") == "x"
        c.close()
    finally:
        os.unlink(path)
