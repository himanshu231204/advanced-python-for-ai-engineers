"""The basic decorator pattern: a function that takes a function and
returns a (usually wrapping) function. `@log_call` above a function is just
sugar for `add = log_call(add)`.

Run: python3 basic_decorator.py
"""
from __future__ import annotations
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


def log_call(fn: Callable[..., R]) -> Callable[..., R]:
    def wrapper(*args: object, **kwargs: object) -> R:
        print(f"calling {fn.__name__}{args}")
        result = fn(*args, **kwargs)
        print(f"{fn.__name__} returned {result!r}")
        return result

    return wrapper


@log_call
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(add(2, 3))
    # calling add(2, 3)
    # add returned 5
    # 5
