"""BROKEN: a logging decorator that calls the wrapped function but
forgets to `return` its result -- every decorated call silently becomes
`None`, no matter what the real function returns.

Run: python3 broken.py
"""
from __future__ import annotations
from functools import wraps
from typing import Callable, TypeVar

R = TypeVar("R")


def logged(fn: Callable[..., R]) -> Callable[..., R]:
    @wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> R:
        print(f"calling {fn.__name__}")
        fn(*args, **kwargs)  # BUG: result is discarded, not returned

    return wrapper


@logged
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    result = add(2, 3)
    print(f"result: {result}")  # None -- the real return value (5) was silently dropped
