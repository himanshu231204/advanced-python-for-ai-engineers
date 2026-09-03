"""Higher-order functions: functions that take or return other functions.

Run: python3 higher_order_functions.py
"""
from __future__ import annotations
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


def apply_to_each(items: list[T], fn: Callable[[T], R]) -> list[R]:
    return [fn(item) for item in items]


def with_logging(fn: Callable[..., R]) -> Callable[..., R]:
    """A tiny preview of module 06 (decorators) using a plain wrapper function
    -- no @syntax yet, just a function that takes and returns a function."""

    def wrapper(*args: object, **kwargs: object) -> R:
        print(f"calling {fn.__name__}{args}")
        result = fn(*args, **kwargs)
        print(f"{fn.__name__} -> {result!r}")
        return result

    return wrapper


if __name__ == "__main__":
    lengths = apply_to_each(["rag", "agents", "async"], len)
    print(lengths)  # [3, 6, 5]

    def word_count(text: str) -> int:
        return len(text.split())

    logged_word_count = with_logging(word_count)
    logged_word_count("advanced python for ai engineers")
    # calling word_count('advanced python for ai engineers',)
    # word_count -> 5
