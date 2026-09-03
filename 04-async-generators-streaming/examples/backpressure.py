"""Backpressure basics: a bounded asyncio.Queue makes a fast producer wait
for a slow consumer instead of piling up unbounded memory.

Run: python3 backpressure.py
"""
from __future__ import annotations
import asyncio


async def producer(queue: asyncio.Queue[int | None], count: int) -> None:
    for i in range(count):
        print(f"producing {i}")
        await queue.put(i)  # blocks once the queue is full -- this IS backpressure
        print(f"produced {i}")
    await queue.put(None)  # sentinel: no more items


async def consumer(queue: asyncio.Queue[int | None]) -> None:
    while True:
        item = await queue.get()
        if item is None:
            break
        await asyncio.sleep(0.2)  # simulate slow downstream work (e.g. writing to a DB)
        print(f"consumed {item}")


async def main() -> None:
    queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=2)  # small buffer -> visible backpressure
    await asyncio.gather(producer(queue, 5), consumer(queue))


if __name__ == "__main__":
    asyncio.run(main())
