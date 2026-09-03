"""Bounded vs unbounded asyncio.Queue: an unbounded queue lets a fast
producer pile up unlimited unprocessed items in memory if the consumer
falls behind; a bounded queue (maxsize=N) makes the producer's `put()`
await until there's room -- backpressure, not a crash.

Run: python3 bounded_vs_unbounded_queue.py
"""
from __future__ import annotations
import asyncio
import contextlib


async def fast_producer(queue: asyncio.Queue[int], count: int) -> None:
    for i in range(count):
        await queue.put(i)


async def run_and_inspect(queue: asyncio.Queue[int], *, label: str) -> None:
    producer = asyncio.create_task(fast_producer(queue, 20))
    await asyncio.sleep(0.02)  # give the producer a head start; nothing consumes the queue
    print(f"{label}: queue size after 0.02s = {queue.qsize()}")
    producer.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await producer


async def main() -> None:
    await run_and_inspect(asyncio.Queue(), label="unbounded")  # no maxsize -- unlimited buffering
    await run_and_inspect(asyncio.Queue(maxsize=3), label="bounded (maxsize=3)")


if __name__ == "__main__":
    asyncio.run(main())
