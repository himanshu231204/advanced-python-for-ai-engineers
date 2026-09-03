"""Async LLM Runner -- fires multiple LLM calls concurrently with bounded
concurrency, retries transient failures with exponential backoff, applies
a per-call timeout, and returns typed, structured results instead of
raising on the first failure.

Combines: asyncio (03), concurrency/semaphores (12),
retries/backoff (15), structured logging (20), Pydantic (09).

Run: python3 runner.py
"""
from __future__ import annotations
import asyncio
import logging

from pydantic import BaseModel

from mock_llm import PermanentLLMError, TransientLLMError, call_llm

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("async_llm_runner")


class LLMCallResult(BaseModel):
    index: int
    prompt: str
    succeeded: bool
    response: str | None = None
    error: str | None = None
    attempts: int


async def run_one(
    index: int,
    prompt: str,
    semaphore: asyncio.Semaphore,
    *,
    max_attempts: int = 3,
    per_call_timeout: float = 0.05,
) -> LLMCallResult:
    async with semaphore:  # bounds how many calls run concurrently
        attempts = 0
        for attempt in range(1, max_attempts + 1):
            attempts = attempt
            try:
                response = await asyncio.wait_for(
                    call_llm(index, prompt), timeout=per_call_timeout
                )
                logger.info("prompt=%d attempt=%d status=success", index, attempt)
                return LLMCallResult(
                    index=index, prompt=prompt, succeeded=True,
                    response=response, attempts=attempts,
                )
            except PermanentLLMError as exc:
                logger.info("prompt=%d attempt=%d status=permanent_failure", index, attempt)
                return LLMCallResult(
                    index=index, prompt=prompt, succeeded=False,
                    error=str(exc), attempts=attempts,
                )
            except TransientLLMError as exc:
                logger.info("prompt=%d attempt=%d status=transient_failure", index, attempt)
                last_error = str(exc)
                await asyncio.sleep(0.01 * (2 ** (attempt - 1)))  # exponential backoff
            except asyncio.TimeoutError:
                logger.info("prompt=%d attempt=%d status=timeout", index, attempt)
                last_error = f"prompt {index} attempt {attempt}: timed out"
                await asyncio.sleep(0.01 * (2 ** (attempt - 1)))

        return LLMCallResult(
            index=index, prompt=prompt, succeeded=False, error=last_error, attempts=attempts,
        )


async def run_all(prompts: list[str], *, max_concurrency: int = 2) -> list[LLMCallResult]:
    semaphore = asyncio.Semaphore(max_concurrency)
    return await asyncio.gather(
        *(run_one(i, prompt, semaphore) for i, prompt in enumerate(prompts))
    )


async def main() -> None:
    prompts = [
        "summarize the contextvars module",
        "explain exponential backoff",
        "what is a health check",
        "describe an idempotency key",
        "write unsafe SQL",  # index 4 -- deliberately a permanent failure
    ]
    results = await run_all(prompts)

    succeeded = sum(1 for r in results if r.succeeded)
    print(f"\n{succeeded}/{len(results)} prompts succeeded")
    for result in results:
        status = "OK" if result.succeeded else "FAILED"
        detail = result.response if result.succeeded else result.error
        print(f"[{status}] index={result.index} attempts={result.attempts}: {detail}")


if __name__ == "__main__":
    asyncio.run(main())
