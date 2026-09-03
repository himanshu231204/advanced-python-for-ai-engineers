"""A minimal TTL cache -- avoids repeating an (expensive, billed) LLM call
for a request the service has already answered recently.
"""
from __future__ import annotations
import time


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str) -> None:
        self._store[key] = (time.monotonic() + self._ttl, value)
