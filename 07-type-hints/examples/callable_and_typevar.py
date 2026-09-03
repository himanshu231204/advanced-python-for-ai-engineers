"""`Callable` types a function value's signature; `TypeVar` writes a generic
function whose input and output types are linked. A deeper dive into
generics and `Protocol` lives in 11-protocols-generics -- this is just
enough to use them correctly.

Run: python3 callable_and_typevar.py
"""
from __future__ import annotations
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


def apply_twice(fn: Callable[[T], T], value: T) -> T:
    """`fn` must take and return the SAME type `T` -- the type checker will
    reject `apply_twice(str.upper, 5)` even though this function never runs."""
    return fn(fn(value))


def map_results(items: list[T], transform: Callable[[T], R]) -> list[R]:
    return [transform(item) for item in items]


if __name__ == "__main__":
    print(apply_twice(lambda x: x * 2, 3))  # 12
    print(apply_twice(str.upper, "ab"))  # AB (upper of an already-upper string)

    lengths: list[int] = map_results(["rag", "agents"], len)
    print(lengths)  # [3, 6]
