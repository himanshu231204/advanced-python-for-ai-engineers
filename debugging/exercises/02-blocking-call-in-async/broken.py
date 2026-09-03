"""BROKEN: uses time.sleep() (a BLOCKING call) inside an async function.
This freezes the entire event loop for its duration -- no other task can
run concurrently, defeating the entire point of asyncio.

Run: python3 broken.py
"""
from __future__ import annotations
import asyncio
import time


async def slow_task(name: str) -> None:
    print(f"{name} start")
    time.sleep(0.05)  # BUG: blocks the whole event loop, not just this task
    print(f"{name} end")


async def main() -> None:
    start = time.perf_counter()
    await asyncio.gather(slow_task("A"), slow_task("B"))
    elapsed = time.perf_counter() - start
    print(f"elapsed: {elapsed:.2f}s")  # ~0.10s -- ran SEQUENTIALLY, not concurrently


if __name__ == "__main__":
    asyncio.run(main())
