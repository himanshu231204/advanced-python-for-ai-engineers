"""FIXED: only retry exceptions known to be transient; let non-retryable
errors fail immediately, on the first attempt.

Run: python3 fixed.py
"""
from __future__ import annotations
import time


class InvalidApiKeyError(Exception):
    """Not retryable -- fail fast."""


class RateLimitedError(Exception):
    """Retryable -- the request will likely succeed after a short wait."""


def call_llm_api(attempt_count: list[int]) -> str:
    attempt_count[0] += 1
    raise InvalidApiKeyError("the configured API key was rejected")


def call_with_retry(max_attempts: int = 3) -> str:
    attempt_count = [0]
    for _ in range(max_attempts):
        try:
            return call_llm_api(attempt_count)
        except RateLimitedError:  # FIX: only retry the transient error type
            time.sleep(0.01)
            continue
        except InvalidApiKeyError as exc:
            raise RuntimeError(f"failed after {attempt_count[0]} attempt(s)") from exc
    raise RuntimeError("exhausted retries")


if __name__ == "__main__":
    try:
        call_with_retry()
    except RuntimeError as exc:
        print(str(exc))  # failed after 1 attempt(s) -- no wasted retries
