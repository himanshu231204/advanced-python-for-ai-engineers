"""AI Engineering Example -- why asyncio helps I/O-bound work.

Simulates calling an LLM, a vector DB, and a search API for one user request.
Each call is pure I/O wait (represented here with `asyncio.sleep`, standing
in for a real network round-trip). Awaiting them one at a time pays for every
wait in sequence; gathering them lets Python start all three waits together.

Run: python3 fanout_io_bound.py
"""
from __future__ import annotations
import asyncio
import time

CALLS = [("llm", 0.5), ("vector_db", 0.3), ("search_api", 0.4)]


async def fake_api_call(name: str, delay: float) -> str:
    await asyncio.sleep(delay)  # stand-in for a real HTTP call (see 13-httpx-async-http)
    return f"{name} result"


async def sequential() -> list[str]:
    results = []
    for name, delay in CALLS:
        results.append(await fake_api_call(name, delay))
    return results


async def concurrent() -> list[str]:
    return await asyncio.gather(*(fake_api_call(name, delay) for name, delay in CALLS))


async def main() -> None:
    start = time.perf_counter()
    await sequential()
    print(f"sequential: {time.perf_counter() - start:.2f}s (sum of all delays: ~1.2s)")

    start = time.perf_counter()
    await concurrent()
    print(f"concurrent: {time.perf_counter() - start:.2f}s (slowest single delay: ~0.5s)")


if __name__ == "__main__":
    asyncio.run(main())
