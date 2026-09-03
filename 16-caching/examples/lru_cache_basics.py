"""functools.cache / lru_cache: memoize a pure function's results, keyed
by its exact arguments. `cache` is `lru_cache(maxsize=None)` -- unbounded;
`lru_cache(maxsize=N)` evicts the Least Recently Used entry once full.

Run: python3 lru_cache_basics.py
"""
from __future__ import annotations
from functools import cache, lru_cache

calls = {"count": 0}


@cache
def expensive_computation(n: int) -> int:
    calls["count"] += 1
    return n * n


@lru_cache(maxsize=2)
def bounded_cache(n: int) -> int:
    return n * 10


if __name__ == "__main__":
    print(expensive_computation(4))  # runs the function, calls=1
    print(expensive_computation(4))  # cache hit, calls STILL 1
    print(expensive_computation(5))  # new args, runs again, calls=2
    print("actual calls:", calls["count"])  # 2, not 3

    print(expensive_computation.cache_info())
    # CacheInfo(hits=1, misses=2, maxsize=None, currsize=2)

    # maxsize=2 -- the third distinct key evicts the least recently used one
    bounded_cache(1)
    bounded_cache(2)
    bounded_cache(3)  # evicts bounded_cache(1)'s cached entry
    print(bounded_cache.cache_info())
    # CacheInfo(hits=0, misses=3, maxsize=2, currsize=2)
