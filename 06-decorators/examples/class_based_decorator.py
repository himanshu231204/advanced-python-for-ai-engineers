"""A class-based decorator: any object with __call__ can decorate a
function. Useful when the decorator needs to hold state across calls.

Run: python3 class_based_decorator.py
"""
from __future__ import annotations
import functools
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


class CountCalls:
    def __init__(self, fn: Callable[..., R]) -> None:
        functools.update_wrapper(self, fn)  # class-based equivalent of functools.wraps
        self.fn = fn
        self.calls = 0

    def __call__(self, *args: object, **kwargs: object) -> R:
        self.calls += 1
        print(f"{self.fn.__name__} has been called {self.calls} time(s)")
        return self.fn(*args, **kwargs)


@CountCalls
def ping() -> str:
    return "pong"


if __name__ == "__main__":
    print(ping())
    print(ping())
    print("total calls:", ping.calls)
