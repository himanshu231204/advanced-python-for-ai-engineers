"""`yield from` delegates iteration to a sub-generator/sub-iterable, without
writing a manual for-loop to re-yield each item.

Run: python3 yield_from.py
"""
from __future__ import annotations
from collections.abc import Iterator


def vector_search(query: str) -> Iterator[str]:
    yield f"[vector] result for {query!r} #1"
    yield f"[vector] result for {query!r} #2"


def keyword_search(query: str) -> Iterator[str]:
    yield f"[keyword] result for {query!r} #1"


def hybrid_search(query: str) -> Iterator[str]:
    """Delegates to two underlying generators -- the caller just sees one
    combined stream of results, in order."""
    yield from vector_search(query)
    yield from keyword_search(query)


if __name__ == "__main__":
    for result in hybrid_search("async generators"):
        print(result)
    # [vector] result for 'async generators' #1
    # [vector] result for 'async generators' #2
    # [keyword] result for 'async generators' #1
