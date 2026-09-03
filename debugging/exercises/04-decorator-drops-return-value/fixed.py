"""FIXED: return the wrapped function's result from the wrapper.

Run: python3 fixed.py
"""
from __future__ import annotations
from functools import wraps
from typing import Callable, TypeVar

R = TypeVar("R")


def logged(fn: Callable[..., R]) -> Callable[..., R]:
    @wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> R:
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)  # FIX: return the real result

    return wrapper


@logged
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    result = add(2, 3)
    print(f"result: {result}")  # 5
