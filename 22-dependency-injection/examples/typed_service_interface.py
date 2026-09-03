"""A typed service interface (via Protocol, module 11) lets dependency
injection be type-checked: any function/class that says it needs an
`Embedder` can accept ANY object satisfying that shape, real or fake.

Run: python3 typed_service_interface.py
"""
from __future__ import annotations
from typing import Protocol


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class RemoteEmbedder:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]  # pretend API call


class DeterministicFakeEmbedder:
    def embed(self, text: str) -> list[float]:
        return [float(len(text))]  # cheap, deterministic -- ideal for tests


class DocumentIndexer:
    """Depends on the Embedder INTERFACE, not any specific implementation."""

    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder

    def index(self, text: str) -> list[float]:
        return self._embedder.embed(text)


if __name__ == "__main__":
    production_indexer = DocumentIndexer(embedder=RemoteEmbedder())
    print(production_indexer.index("hello"))

    test_indexer = DocumentIndexer(embedder=DeterministicFakeEmbedder())
    print(test_indexer.index("hello"))  # deterministic, no network call
