"""AI Engineering Example -- fanning out many concurrent LLM calls SAFELY:
bounded concurrency (a semaphore, so you don't open hundreds of connections
at once or blow through a rate limit), a per-call timeout, and errors
collected per-request instead of one failure crashing the whole batch.

Run: python3 bounded_llm_fanout.py
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass


@dataclass
class CallResult:
    prompt: str
    output: str | None
    error: str | None


async def call_llm(prompt: str) -> str:
    if prompt == "slow":
        await asyncio.sleep(1)  # simulate a hung request
    if prompt == "bad":
        raise RuntimeError("simulated API error")
    await asyncio.sleep(0.05)
    return f"response to {prompt!r}"


async def safe_call(sem: asyncio.Semaphore, prompt: str, *, per_call_timeout: float) -> CallResult:
    async with sem:
        try:
            async with asyncio.timeout(per_call_timeout):
                output = await call_llm(prompt)
            return CallResult(prompt=prompt, output=output, error=None)
        except TimeoutError:
            return CallResult(prompt=prompt, output=None, error="timed out")
        except Exception as e:  # deliberately broad -- this boundary must never crash the batch
            return CallResult(prompt=prompt, output=None, error=str(e))


async def run_batch(prompts: list[str], *, max_concurrent: int, per_call_timeout: float) -> list[CallResult]:
    sem = asyncio.Semaphore(max_concurrent)
    return await asyncio.gather(*(safe_call(sem, p, per_call_timeout=per_call_timeout) for p in prompts))


async def main() -> None:
    prompts = ["hello", "slow", "bad", "world"]
    results = await run_batch(prompts, max_concurrent=2, per_call_timeout=0.2)
    for r in results:
        status = r.output if r.error is None else f"FAILED: {r.error}"
        print(f"{r.prompt!r} -> {status}")


if __name__ == "__main__":
    asyncio.run(main())
