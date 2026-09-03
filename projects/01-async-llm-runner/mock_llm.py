"""A deterministic stand-in for a real LLM API client -- no network calls,
so the project runs offline and its output is reproducible. Real code
would replace this with an httpx.AsyncClient call to an actual provider.
"""
from __future__ import annotations
import asyncio


class TransientLLMError(Exception):
    """Simulates a retryable failure (e.g. a 503 or rate limit)."""


class PermanentLLMError(Exception):
    """Simulates a non-retryable failure (e.g. a content policy rejection)."""


# prompt index -> how many times it fails before succeeding (0 = succeeds immediately)
_FAILS_BEFORE_SUCCESS = {1: 1, 3: 10}  # index 3 never recovers -- exceeds max_attempts
_PERMANENT_FAILURES = {4}

_attempt_counts: dict[int, int] = {}


async def call_llm(index: int, prompt: str, *, call_delay: float = 0.02) -> str:
    """Pretends to call an LLM. Deterministic per-index behavior lets this
    example demonstrate retries, permanent failures, and timeouts without
    any randomness."""
    _attempt_counts[index] = _attempt_counts.get(index, 0) + 1
    attempt = _attempt_counts[index]

    if index in _PERMANENT_FAILURES:
        raise PermanentLLMError(f"prompt {index} rejected by content policy")

    if attempt <= _FAILS_BEFORE_SUCCESS.get(index, 0):
        raise TransientLLMError(f"prompt {index} attempt {attempt}: rate limited")

    await asyncio.sleep(call_delay)
    return f"response to {prompt!r} (succeeded on attempt {attempt})"
