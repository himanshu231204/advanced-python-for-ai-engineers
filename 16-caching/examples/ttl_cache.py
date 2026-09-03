"""functools.cache/lru_cache never expire on their own -- for that you
need a TTL (time-to-live) cache: each entry is valid for a fixed duration,
after which the next lookup recomputes it. This is a minimal hand-rolled
version showing the mechanism (production code would reach for a library).

Run: python3 ttl_cache.py
"""
from __future__ import annotations
import time
from typing import Callable, TypeVar

R = TypeVar("R")


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[object, tuple[float, object]] = {}

    def get_or_compute(self, key: object, compute: Callable[[], R]) -> R:
        now = time.monotonic()
        if key in self._store:
            expires_at, value = self._store[key]
            if now < expires_at:
                return value  # type: ignore[return-value]
        value = compute()
        self._store[key] = (now + self.ttl_seconds, value)
        return value


if __name__ == "__main__":
    cache = TTLCache(ttl_seconds=0.2)
    calls = {"count": 0}

    def compute() -> str:
        calls["count"] += 1
        return f"computed #{calls['count']}"

    print(cache.get_or_compute("key", compute))  # computed #1
    print(cache.get_or_compute("key", compute))  # computed #1 -- still fresh

    time.sleep(0.25)  # let the TTL expire

    print(cache.get_or_compute("key", compute))  # computed #2 -- recomputed
