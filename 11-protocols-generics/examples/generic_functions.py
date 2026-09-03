"""Generic functions with PEP 695 syntax: `def first[T](...)` declares the
type parameter inline, linking the parameter and return types without a
separate TypeVar() definition.

Requires: Python 3.12+
Run: python3.12 generic_functions.py
"""
from __future__ import annotations
from collections.abc import Callable


def first[T](items: list[T]) -> T | None:
    return items[0] if items else None


def map_items[T, R](items: list[T], transform: Callable[[T], R]) -> list[R]:
    return [transform(item) for item in items]


if __name__ == "__main__":
    print(first([3, 1, 2]))  # 3
    print(first([]))  # None

    print(map_items(["rag", "agents"], len))  # [3, 6]
