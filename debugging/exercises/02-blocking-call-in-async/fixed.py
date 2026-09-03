"""FIXED: use asyncio.sleep() (a non-blocking await) instead of
time.sleep(). This yields control back to the event loop, letting the
other gathered task actually run while this one "sleeps."

Run: python3 fixed.py
"""
from __future__ import annotations
import asyncio
import time


async def slow_task(name: str) -> None:
    print(f"{name} start")
    await asyncio.sleep(0.05)  # FIX: non-blocking -- yields to the event loop
    print(f"{name} end")


async def main() -> None:
    start = time.perf_counter()
    await asyncio.gather(slow_task("A"), slow_task("B"))
    elapsed = time.perf_counter() - start
    print(f"elapsed: {elapsed:.2f}s")  # ~0.05s -- ran CONCURRENTLY


if __name__ == "__main__":
    asyncio.run(main())
