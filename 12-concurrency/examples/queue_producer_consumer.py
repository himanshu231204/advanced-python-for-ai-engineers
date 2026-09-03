"""asyncio.Queue coordinates a producer and multiple worker consumers --
the standard shape for a background job pipeline (see
17-queues-background-tasks for the broader pattern).

Run: python3 queue_producer_consumer.py
"""
from __future__ import annotations
import asyncio


async def producer(queue: asyncio.Queue[str], jobs: list[str]) -> None:
    for job in jobs:
        await queue.put(job)


async def worker(name: str, queue: asyncio.Queue[str], results: list[str]) -> None:
    while True:
        job = await queue.get()
        await asyncio.sleep(0.05)  # pretend work
        results.append(f"{name} processed {job}")
        queue.task_done()


async def main() -> None:
    queue: asyncio.Queue[str] = asyncio.Queue()
    jobs = [f"job-{i}" for i in range(6)]
    results: list[str] = []

    await producer(queue, jobs)

    workers = [asyncio.create_task(worker(f"worker-{i}", queue, results)) for i in range(3)]

    await queue.join()  # wait until every item has been processed
    for w in workers:
        w.cancel()  # workers loop forever -- cancel them once the queue is drained

    print(f"processed {len(results)} jobs across {len(workers)} workers")
    for line in sorted(results):
        print(" ", line)


if __name__ == "__main__":
    asyncio.run(main())
