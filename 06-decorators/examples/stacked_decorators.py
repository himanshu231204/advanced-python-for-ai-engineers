"""AI Engineering Example -- stacking retry + logging + timing decorators
around an LLM call, and observing the order they execute in.

Decorators apply bottom-up but EXECUTE outer-to-inner:

    @timed
    @logged
    @retry(times=2)
    def call_llm(): ...

is equivalent to `call_llm = timed(logged(retry(times=2)(call_llm)))`, so at
call time: timed starts -> logged starts -> retry runs (and may loop) ->
logged ends -> timed ends.

Run: python3 stacked_decorators.py
"""
from __future__ import annotations
import functools
import time
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


def timed(fn: Callable[..., R]) -> Callable[..., R]:
    @functools.wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> R:
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        print(f"[timed] {fn.__name__} took {time.perf_counter() - start:.3f}s")
        return result

    return wrapper


def logged(fn: Callable[..., R]) -> Callable[..., R]:
    @functools.wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> R:
        print(f"[logged] calling {fn.__name__}")
        result = fn(*args, **kwargs)
        print(f"[logged] {fn.__name__} returned {result!r}")
        return result

    return wrapper


def retry(times: int) -> Callable[[Callable[..., R]], Callable[..., R]]:
    def decorator(fn: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(fn)
        def wrapper(*args: object, **kwargs: object) -> R:
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:  # deliberately broad for this demo
                    print(f"[retry] attempt {attempt} failed: {e}")
            raise RuntimeError("all retries exhausted")

        return wrapper

    return decorator


_state = {"attempts": 0}


@timed
@logged
@retry(times=2)
def call_llm(prompt: str) -> str:
    _state["attempts"] += 1
    if _state["attempts"] < 2:
        raise RuntimeError("simulated rate limit")
    return f"response to: {prompt}"


if __name__ == "__main__":
    print(call_llm("hello"))
