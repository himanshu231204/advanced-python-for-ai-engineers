"""Structural typing with Protocol: unrelated classes satisfy the same
type just by having the right methods -- no shared base class needed.
@runtime_checkable additionally lets isinstance() check a Protocol
directly (checking method presence only, not signatures).

Run: python3 structural_typing.py
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class LocalHashEmbedder:
    """Never imports or inherits from Embedder -- it satisfies the
    protocol purely by shape."""

    def embed(self, text: str) -> list[float]:
        return [float(len(text) % 10)]


class RemoteApiEmbedder:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]  # pretend API call


def embed_all(embedder: Embedder, texts: list[str]) -> list[list[float]]:
    return [embedder.embed(t) for t in texts]


if __name__ == "__main__":
    print(embed_all(LocalHashEmbedder(), ["hi", "hello"]))
    print(embed_all(RemoteApiEmbedder(), ["hi"]))

    print(isinstance(LocalHashEmbedder(), Embedder))  # True -- structural check
    print(isinstance("not an embedder", Embedder))  # False
