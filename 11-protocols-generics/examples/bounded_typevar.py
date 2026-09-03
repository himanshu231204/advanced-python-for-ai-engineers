"""A bounded type parameter restricts what T can be -- here, anything with
an `id: str` attribute -- so the generic class can rely on `.id` existing
without knowing the concrete type in advance.

Requires: Python 3.12+
Run: python3.12 bounded_typevar.py
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


class HasId(Protocol):
    id: str


class Repository[T: HasId]:
    """T is bounded to HasId -- a type checker allows `.id` access below
    for ANY T, because every valid T is guaranteed to have it."""

    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def add(self, item: T) -> None:
        self._items[item.id] = item  # only valid because T is bounded by HasId

    def get(self, item_id: str) -> T | None:
        return self._items.get(item_id)


@dataclass
class Document:
    id: str
    text: str


if __name__ == "__main__":
    repo: Repository[Document] = Repository()
    repo.add(Document(id="doc-1", text="Bounded TypeVars restrict generic params."))

    found = repo.get("doc-1")
    print(found)
    print(repo.get("missing"))  # None
