"""Common mistake: calling a blocking function (`time.sleep`) inside async
code. It doesn't just block its own coroutine -- it freezes the ENTIRE event
loop, so no other coroutine can make progress either.

Run: python3 blocking_vs_nonblocking.py
"""
from __future__ import annotations
import asyncio
import time


async def blocking_worker(name: str) -> None:
    print(f"{name} start")
    time.sleep(1)  # WRONG -- blocks the whole event loop, not just this coroutine
    print(f"{name} done")


async def nonblocking_worker(name: str) -> None:
    print(f"{name} start")
    await asyncio.sleep(1)  # BETTER -- yields control back to the event loop
    print(f"{name} done")


async def main() -> None:
    start = time.perf_counter()
    await asyncio.gather(blocking_worker("A"), blocking_worker("B"))
    print(f"blocking total: {time.perf_counter() - start:.2f}s (expect ~2s, NOT concurrent)\n")

    start = time.perf_counter()
    await asyncio.gather(nonblocking_worker("A"), nonblocking_worker("B"))
    print(f"non-blocking total: {time.perf_counter() - start:.2f}s (expect ~1s, concurrent)")


if __name__ == "__main__":
    asyncio.run(main())
