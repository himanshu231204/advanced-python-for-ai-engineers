"""Generator functions: `yield` pauses and resumes function execution instead
of running to completion and returning everything at once.

Run: python3 generator_basics.py
"""
from __future__ import annotations
from collections.abc import Iterator


def paginate(items: list[str], page_size: int) -> Iterator[list[str]]:
    """Same behavior as `iterator_protocol.Paginator`, written as a generator
    -- far less boilerplate for the exact same lazy, one-page-at-a-time
    iteration."""
    for start in range(0, len(items), page_size):
        yield items[start : start + page_size]


if __name__ == "__main__":
    docs = [f"doc-{i}" for i in range(7)]

    gen = paginate(docs, page_size=3)
    print(next(gen))  # ['doc-0', 'doc-1', 'doc-2']
    print(next(gen))  # ['doc-3', 'doc-4', 'doc-5']

    # A generator is exhausted after StopIteration -- this is a *new* one.
    for page in paginate(docs, page_size=3):
        print(page)
