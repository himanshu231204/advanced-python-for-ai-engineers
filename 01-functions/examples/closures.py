"""Closures -- functions that remember the environment they were created in.

Run: python3 closures.py
"""
from __future__ import annotations
from collections.abc import Callable


def make_rate_limiter(max_calls: int) -> Callable[[], bool]:
    """Return a closure that tracks call count via captured state.

    `calls_made` lives in `make_rate_limiter`'s scope, not `allow_call`'s --
    each call to `make_rate_limiter` creates a fresh, isolated counter.
    """
    calls_made = 0

    def allow_call() -> bool:
        nonlocal calls_made
        if calls_made >= max_calls:
            return False
        calls_made += 1
        return True

    return allow_call


if __name__ == "__main__":
    allow = make_rate_limiter(max_calls=3)
    results = [allow() for _ in range(5)]
    print(results)  # [True, True, True, False, False]

    # A second limiter has its own independent counter.
    another = make_rate_limiter(max_calls=1)
    print(another(), another())  # True False
