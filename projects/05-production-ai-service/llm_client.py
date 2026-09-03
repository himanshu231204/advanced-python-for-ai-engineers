"""A deterministic, offline LLM client with retry + timeout handling --
stands in for a real provider call over httpx.
"""
from __future__ import annotations
import asyncio

from config import settings


class LLMTimeoutError(Exception):
    pass


async def _call_provider(text: str) -> str:
    await asyncio.sleep(0.01)
    return f"summary: {text[:20]}"


async def summarize(text: str, *, max_attempts: int = 2) -> str:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await asyncio.wait_for(_call_provider(text), timeout=settings.llm_timeout_seconds)
        except asyncio.TimeoutError as exc:
            last_error = exc
            await asyncio.sleep(0.01 * attempt)
    raise LLMTimeoutError(f"LLM call timed out after {max_attempts} attempt(s)") from last_error
