"""A pool of background workers pulling jobs from one shared queue --
the standard shape for processing long-running AI jobs (batch embedding,
evaluation runs) outside the request/response cycle.

Run: python3 background_worker_pool.py
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass


@dataclass
class Job:
    id: str
    payload: str


async def process_job(job: Job) -> str:
    await asyncio.sleep(0.05)  # pretend this is a slow embedding/inference call
    return f"processed {job.id}: {job.payload.upper()}"


async def worker(name: str, queue: asyncio.Queue[Job | None], results: list[str]) -> None:
    while True:
        job = await queue.get()
        if job is None:  # sentinel -- tells this worker to stop
            queue.task_done()
            break
        results.append(await process_job(job))
        queue.task_done()


async def run_pool(jobs: list[Job], *, num_workers: int) -> list[str]:
    queue: asyncio.Queue[Job | None] = asyncio.Queue()
    results: list[str] = []

    workers = [
        asyncio.create_task(worker(f"worker-{i}", queue, results)) for i in range(num_workers)
    ]

    for job in jobs:
        await queue.put(job)
    for _ in workers:
        await queue.put(None)  # one stop-sentinel per worker

    await asyncio.gather(*workers)
    return results


if __name__ == "__main__":
    jobs = [Job(id=f"job-{i}", payload=f"doc-{i}") for i in range(6)]
    results = asyncio.run(run_pool(jobs, num_workers=3))
    print(f"processed {len(results)} jobs")
    for line in sorted(results):
        print(" ", line)
