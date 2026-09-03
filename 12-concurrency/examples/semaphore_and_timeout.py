"""asyncio.Semaphore caps how many coroutines run at once (concurrency
limiting); asyncio.timeout (3.11+) bounds how long a single await may take,
raising TimeoutError if it's exceeded.

Run: python3 semaphore_and_timeout.py
"""
from __future__ import annotations
import asyncio

running = 0
max_seen = 0


async def limited_call(sem: asyncio.Semaphore, delay: float) -> None:
    global running, max_seen
    async with sem:  # blocks here once `sem`'s permits are exhausted
        running += 1
        max_seen = max(max_seen, running)
        await asyncio.sleep(delay)
        running -= 1


async def demo_semaphore() -> None:
    sem = asyncio.Semaphore(3)  # at most 3 concurrent calls allowed
    await asyncio.gather(*(limited_call(sem, 0.1) for _ in range(10)))
    print(f"max concurrent calls observed: {max_seen} (limit was 3)")


async def slow_call() -> str:
    await asyncio.sleep(1)
    return "too slow"


async def demo_timeout() -> None:
    try:
        async with asyncio.timeout(0.1):
            await slow_call()
    except TimeoutError:
        print("caught: call exceeded its 0.1s timeout")


async def main() -> None:
    await demo_semaphore()
    await demo_timeout()


if __name__ == "__main__":
    asyncio.run(main())
