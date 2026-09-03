"""The iterator protocol: __iter__ and __next__.

Run: python3 iterator_protocol.py
"""
from __future__ import annotations


class Paginator:
    """A custom iterator that yields fixed-size pages from a list."""

    def __init__(self, items: list[str], page_size: int) -> None:
        self._items = items
        self._page_size = page_size
        self._index = 0

    def __iter__(self) -> "Paginator":
        return self

    def __next__(self) -> list[str]:
        if self._index >= len(self._items):
            raise StopIteration
        page = self._items[self._index : self._index + self._page_size]
        self._index += self._page_size
        return page


if __name__ == "__main__":
    docs = [f"doc-{i}" for i in range(7)]
    for page in Paginator(docs, page_size=3):
        print(page)
    # ['doc-0', 'doc-1', 'doc-2']
    # ['doc-3', 'doc-4', 'doc-5']
    # ['doc-6']
