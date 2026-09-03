"""Exponential backoff with jitter: each retry waits roughly twice as long
as the last, plus a small random amount (jitter) so many clients retrying
at once don't all hammer the server at exactly the same moments.

Run: python3 exponential_backoff_jitter.py
"""
from __future__ import annotations
import asyncio
import random


class RetryableError(Exception):
    pass


def backoff_delay(attempt: int, *, base: float = 0.1, cap: float = 5.0) -> float:
    """attempt starts at 1. Delay grows as base * 2^(attempt-1), capped,
    plus up to 50% extra random jitter."""
    exponential = min(cap, base * (2 ** (attempt - 1)))
    jitter = random.uniform(0, exponential * 0.5)
    return exponential + jitter


async def call_with_backoff(flaky_call, *, max_attempts: int = 5) -> str:
    for attempt in range(1, max_attempts + 1):
        try:
            return await flaky_call()
        except RetryableError as e:
            if attempt == max_attempts:
                raise
            delay = backoff_delay(attempt)
            print(f"attempt {attempt} failed ({e}); sleeping {delay:.2f}s")
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")


_calls = {"count": 0}


async def flaky() -> str:
    _calls["count"] += 1
    if _calls["count"] < 3:
        raise RetryableError("simulated transient failure")
    return "success"


if __name__ == "__main__":
    print("delays for attempts 1-4:", [round(backoff_delay(a), 2) for a in range(1, 5)])
    print(asyncio.run(call_with_backoff(flaky)))
