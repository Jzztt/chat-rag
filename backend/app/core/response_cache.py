"""Simple in-memory response cache for chat answers."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional

from app.core.config import settings


@dataclass
class ResponseCacheEntry:
    """Metadata for cached responses."""
    data: dict[str, Any]
    created_at: float


class ResponseCache:
    """Thread-safe TTL cache optimized for repeated chat questions."""

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 200):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._cache: dict[str, ResponseCacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Fetch cached response if still valid."""
        if not settings.RESPONSE_CACHE_ENABLED:
            return None

        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            if self.ttl > 0 and (time.time() - entry.created_at) > self.ttl:
                del self._cache[key]
                return None

            return entry.data

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Store response payload in cache."""
        if not settings.RESPONSE_CACHE_ENABLED:
            return

        with self._lock:
            if len(self._cache) >= self.max_entries:
                # Remove oldest entries (simple FIFO).
                keys_to_remove = list(self._cache.keys())[: self.max_entries // 4 or 1]
                for old_key in keys_to_remove:
                    self._cache.pop(old_key, None)

            self._cache[key] = ResponseCacheEntry(data=value, created_at=time.time())

    @staticmethod
    def make_key(question: str, workspace_id: str) -> str:
        """Create a deterministic cache key from question + workspace."""
        raw = f"{workspace_id}:{question}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


# Global cache instance
response_cache = ResponseCache(
    ttl_seconds=settings.RESPONSE_CACHE_TTL,
    max_entries=settings.RESPONSE_CACHE_MAX_ENTRIES,
)

# Convenience function
make_cache_key = ResponseCache.make_key

