"""Cache invalidation strategies: explicit removal, and versioned keys
(bumping a version prefix invalidates every old entry at once without
touching the underlying store).

Run: python3 cache_invalidation.py
"""
from __future__ import annotations


class VersionedCache:
    """Instead of hunting down and deleting every stale key, bump the
    version -- every old-versioned key is now simply unreachable."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._version = 1

    def _key(self, raw_key: str) -> str:
        return f"v{self._version}:{raw_key}"

    def set(self, raw_key: str, value: str) -> None:
        self._store[self._key(raw_key)] = value

    def get(self, raw_key: str) -> str | None:
        return self._store.get(self._key(raw_key))

    def invalidate_all(self) -> None:
        self._version += 1  # every previously-cached key is now unreachable


if __name__ == "__main__":
    cache = VersionedCache()
    cache.set("doc-1", "cached embedding for doc-1")
    print(cache.get("doc-1"))  # cached embedding for doc-1

    cache.invalidate_all()  # e.g. the embedding model was upgraded
    print(cache.get("doc-1"))  # None -- old version's entry is unreachable

    cache.set("doc-1", "recomputed embedding for doc-1")
    print(cache.get("doc-1"))  # recomputed embedding for doc-1

    # Explicit removal is just deleting the current-version key directly.
    del cache._store[cache._key("doc-1")]
    print(cache.get("doc-1"))  # None
