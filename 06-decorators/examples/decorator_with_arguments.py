"""Decorators that take their own arguments need an extra level of nesting:
a function (`retry(times=3)`) that returns the actual decorator.

Run: python3 decorator_with_arguments.py
"""
from __future__ import annotations
import functools
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


def retry(times: int) -> Callable[[Callable[..., R]], Callable[..., R]]:
    def decorator(fn: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(fn)
        def wrapper(*args: object, **kwargs: object) -> R:
            last_error: Exception | None = None
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:  # deliberately broad for this demo
                    last_error = e
                    print(f"attempt {attempt} failed: {e}")
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


_calls = {"count": 0}


@retry(times=3)
def flaky_call() -> str:
    _calls["count"] += 1
    if _calls["count"] < 3:
        raise RuntimeError("simulated transient failure")
    return "success"


if __name__ == "__main__":
    print(flaky_call())
    # attempt 1 failed: simulated transient failure
    # attempt 2 failed: simulated transient failure
    # success
