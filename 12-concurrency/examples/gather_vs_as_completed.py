"""asyncio.gather waits for ALL coroutines and returns results in the
ORIGINAL order; asyncio.as_completed yields each result as soon as it's
ready, in COMPLETION order -- useful when you want to react to the fastest
result first instead of waiting for the slowest.

Run: python3 gather_vs_as_completed.py
"""
from __future__ import annotations
import asyncio

DELAYS = [("slow", 0.3), ("fast", 0.1), ("medium", 0.2)]


async def fake_call(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name


async def with_gather() -> None:
    results = await asyncio.gather(*(fake_call(n, d) for n, d in DELAYS))
    print("gather (original order):", results)  # ['slow', 'fast', 'medium']


async def with_as_completed() -> None:
    order = []
    for coro in asyncio.as_completed([fake_call(n, d) for n, d in DELAYS]):
        order.append(await coro)
    print("as_completed (finish order):", order)  # ['fast', 'medium', 'slow']


async def main() -> None:
    await with_gather()
    await with_as_completed()


if __name__ == "__main__":
    asyncio.run(main())
