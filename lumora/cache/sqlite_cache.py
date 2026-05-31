"""SQLite-backed cache with optional difflib fuzzy matching."""

from __future__ import annotations

import sqlite3
import threading
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from lumora.cache.base import BaseCache, CacheEntry


_SCHEMA = """
CREATE TABLE IF NOT EXISTS lumora_cache (
    key TEXT PRIMARY KEY,
    normalized_prompt TEXT NOT NULL,
    response_content TEXT NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    created_at REAL NOT NULL,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS ix_lumora_cache_created_at
    ON lumora_cache(created_at);
"""


class SQLiteCache(BaseCache):
    def __init__(self, path: str | Path = ".lumora_cache.sqlite") -> None:
        self.path = str(path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def get_exact(self, key: str) -> CacheEntry | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT key, normalized_prompt, response_content, model, provider, created_at, metadata "
                "FROM lumora_cache WHERE key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_entry(row)

    def get_fuzzy(self, normalized_prompt: str, threshold: float) -> CacheEntry | None:
        if threshold <= 0:
            return None
        with self._lock:
            rows = self._conn.execute(
                "SELECT key, normalized_prompt, response_content, model, provider, created_at, metadata "
                "FROM lumora_cache ORDER BY created_at DESC LIMIT 500"
            ).fetchall()
        best: tuple[float, Any] | None = None
        for row in rows:
            ratio = SequenceMatcher(None, normalized_prompt, row[1]).ratio()
            if ratio >= threshold and (best is None or ratio > best[0]):
                best = (ratio, row)
        if best is None:
            return None
        return self._row_to_entry(best[1])

    def put(self, entry: CacheEntry) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO lumora_cache "
                "(key, normalized_prompt, response_content, model, provider, created_at, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.key,
                    entry.normalized_prompt,
                    entry.response_content,
                    entry.model,
                    entry.provider,
                    entry.created_at,
                    self.serialize_metadata(entry.metadata),
                ),
            )
            self._conn.commit()

    def clear(self) -> int:
        with self._lock:
            cur = self._conn.execute("DELETE FROM lumora_cache")
            self._conn.commit()
            return cur.rowcount or 0

    def stats(self) -> dict[str, Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM lumora_cache"
            ).fetchone()
        count, oldest, newest = cur if cur else (0, None, None)
        return {
            "backend": "sqlite",
            "path": self.path,
            "entries": int(count or 0),
            "oldest": oldest,
            "newest": newest,
        }

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except Exception:  # pragma: no cover
                pass

    def _row_to_entry(self, row) -> CacheEntry:
        return CacheEntry(
            key=row[0],
            normalized_prompt=row[1],
            response_content=row[2],
            model=row[3],
            provider=row[4],
            created_at=row[5],
            metadata=self.deserialize_metadata(row[6] or ""),
        )

    @staticmethod
    def now() -> float:
        return time.time()
