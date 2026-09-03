"""Memoization is caching applied SPECIFICALLY to function results keyed
by arguments -- every memoization is a cache, but not every cache is
memoization (an LLM response cache keyed by a custom string, or an HTTP
cache keyed by URL, are caches without being "memoized function calls").

`functools.cache` also requires every argument to be HASHABLE -- this is
the most common wall people hit trying to memoize something.

Run: python3 cache_vs_memoization.py
"""
from __future__ import annotations
from functools import cache


@cache
def word_count(text: str) -> int:
    """Memoization: caching THIS function's output, keyed by its args."""
    return len(text.split())


def cache_lookup(store: dict[str, str], key: str) -> str | None:
    """Caching WITHOUT memoization -- a plain dict acting as a cache, not
    tied to memoizing any particular function call."""
    return store.get(key)


if __name__ == "__main__":
    print(word_count("advanced python for ai engineers"))  # 5
    print(word_count("advanced python for ai engineers"))  # cache hit

    store = {"prompt:hello": "cached response for hello"}
    print(cache_lookup(store, "prompt:hello"))

    # functools.cache requires hashable arguments -- a list breaks it.
    try:
        word_count(["not", "hashable"])  # type: ignore[arg-type]
    except TypeError as e:
        print(f"caught: {e}")
