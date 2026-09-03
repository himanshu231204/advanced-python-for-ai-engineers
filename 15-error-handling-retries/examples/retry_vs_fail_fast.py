"""Deciding whether to retry: check the exception TYPE, not just "did it
fail?" -- retrying a non-retryable error just wastes time and delays the
real, unfixable failure from surfacing.

Run: python3 retry_vs_fail_fast.py
"""
from __future__ import annotations


class RetryableAPIError(Exception):
    pass


class NonRetryableAPIError(Exception):
    pass


def call_api(mode: str) -> str:
    if mode == "rate_limited":
        raise RetryableAPIError("429 Too Many Requests")
    if mode == "bad_auth":
        raise NonRetryableAPIError("401 Unauthorized")
    return "ok"


def call_with_retry(mode: str, *, max_attempts: int = 3) -> str:
    for attempt in range(1, max_attempts + 1):
        try:
            return call_api(mode)
        except RetryableAPIError as e:
            print(f"attempt {attempt}: retryable failure ({e}) -- retrying")
            if attempt == max_attempts:
                raise
        except NonRetryableAPIError as e:
            print(f"non-retryable failure ({e}) -- failing fast, no retry")
            raise


if __name__ == "__main__":
    try:
        call_with_retry("bad_auth")
    except NonRetryableAPIError:
        print("gave up immediately, as expected\n")

    try:
        call_with_retry("rate_limited", max_attempts=2)
    except RetryableAPIError:
        print("exhausted all retries")
