"""AI Engineering Example -- retrying an LLM call correctly: classify the
failure (retryable vs not) using an exception hierarchy, back off with
jitter between retries, and fail fast on anything that retrying can't fix.

Run: python3 llm_retry_with_backoff.py
"""
from __future__ import annotations
import asyncio
import random


class LLMAPIError(Exception):
    pass


class RateLimitError(LLMAPIError):
    """Retryable -- the provider is asking us to slow down."""


class InvalidPromptError(LLMAPIError):
    """NOT retryable -- the request itself is malformed; retrying sends
    the exact same broken request again."""


def backoff_delay(attempt: int, *, base: float = 0.05, cap: float = 2.0) -> float:
    exponential = min(cap, base * (2 ** (attempt - 1)))
    return exponential + random.uniform(0, exponential * 0.5)


_attempts = {"count": 0}


async def call_llm(prompt: str) -> str:
    if prompt == "":
        raise InvalidPromptError("prompt must not be empty")
    _attempts["count"] += 1
    if _attempts["count"] < 3:
        raise RateLimitError("429: rate limited, try again shortly")
    return f"response to: {prompt}"


async def call_llm_with_retry(prompt: str, *, max_attempts: int = 5) -> str:
    for attempt in range(1, max_attempts + 1):
        try:
            return await call_llm(prompt)
        except RateLimitError as e:
            if attempt == max_attempts:
                raise
            delay = backoff_delay(attempt)
            print(f"attempt {attempt}: {e} -- backing off {delay:.2f}s")
            await asyncio.sleep(delay)
        except InvalidPromptError as e:
            print(f"attempt {attempt}: {e} -- not retrying, failing fast")
            raise
    raise AssertionError("unreachable")


async def main() -> None:
    print(await call_llm_with_retry("summarize this document"))

    try:
        await call_llm_with_retry("")
    except InvalidPromptError:
        print("gave up immediately on the invalid prompt, as expected")


if __name__ == "__main__":
    asyncio.run(main())
