"""Why functools.wraps matters: without it, a decorated function loses its
own identity (__name__, __doc__, etc.), which breaks introspection,
debugging output, and tools that rely on it (docs generators, some
frameworks' route/registration logic).

Run: python3 functools_wraps.py
"""
from __future__ import annotations
import functools
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


def without_wraps(fn: Callable[..., R]) -> Callable[..., R]:
    def wrapper(*args: object, **kwargs: object) -> R:
        return fn(*args, **kwargs)

    return wrapper


def with_wraps(fn: Callable[..., R]) -> Callable[..., R]:
    @functools.wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> R:
        return fn(*args, **kwargs)

    return wrapper


@without_wraps
def greet_a(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"


@with_wraps
def greet_b(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet_a.__name__)  # wrapper             <- WRONG, identity lost
    print(greet_a.__doc__)  # None                 <- WRONG, docstring lost

    print(greet_b.__name__)  # greet_b             <- correct
    print(greet_b.__doc__)  # Return a greeting.   <- correct
