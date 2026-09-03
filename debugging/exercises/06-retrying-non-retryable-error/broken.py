"""BROKEN: retries on ANY exception, including errors that will never
succeed no matter how many times you retry (e.g. an invalid API key).
This wastes time/cost and delays surfacing a real, fixable problem.

Run: python3 broken.py
"""
from __future__ import annotations
import time


class InvalidApiKeyError(Exception):
    """Not retryable -- retrying with the same bad key always fails the same way."""


class RateLimitedError(Exception):
    """Retryable -- the request will likely succeed after a short wait."""


def call_llm_api(attempt_count: list[int]) -> str:
    attempt_count[0] += 1
    raise InvalidApiKeyError("the configured API key was rejected")


def call_with_retry(max_attempts: int = 3) -> str:
    attempt_count = [0]
    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            return call_llm_api(attempt_count)
        except Exception as exc:  # BUG: catches and retries EVERYTHING
            last_error = exc
            time.sleep(0.01)
    assert last_error is not None
    raise RuntimeError(f"failed after {attempt_count[0]} attempts") from last_error


if __name__ == "__main__":
    try:
        call_with_retry()
    except RuntimeError as exc:
        print(str(exc))  # failed after 3 attempts -- wasted 2 retries on a fixed API key
