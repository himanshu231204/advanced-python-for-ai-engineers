"""A custom exception hierarchy lets callers catch broadly (any APIError)
or narrowly (just RateLimitError), and lets retry logic ask "is this
retryable?" by checking a TYPE rather than parsing an error message.

Run: python3 exception_hierarchy.py
"""
from __future__ import annotations


class APIError(Exception):
    """Base for every error this client can raise."""


class RetryableAPIError(APIError):
    """Transient -- retrying with backoff is reasonable."""


class RateLimitError(RetryableAPIError):
    pass


class ServerOverloadedError(RetryableAPIError):
    pass


class NonRetryableAPIError(APIError):
    """Retrying will never help -- the request itself is wrong."""


class AuthenticationError(NonRetryableAPIError):
    pass


class InvalidRequestError(NonRetryableAPIError):
    pass


def classify(exc: APIError) -> str:
    if isinstance(exc, RetryableAPIError):
        return "retryable"
    return "not retryable"


if __name__ == "__main__":
    for exc in [RateLimitError("429"), AuthenticationError("401"), ServerOverloadedError("503")]:
        print(f"{type(exc).__name__}: {classify(exc)}")

    # Catching the BASE class catches every subclass beneath it.
    try:
        raise RateLimitError("too many requests")
    except APIError as e:
        print(f"caught via base class: {type(e).__name__}")
