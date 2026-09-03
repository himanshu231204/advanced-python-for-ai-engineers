"""Tracking background job status: a "submit job, poll for status" API
needs somewhere to record pending/running/done/failed for each job ID --
this is the in-memory shape of it (a real system would use a DB or Redis).

Run: python3 job_status_tracking.py
"""
from __future__ import annotations
import asyncio
import uuid
from enum import Enum, auto


class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
    FAILED = auto()


class JobStore:
    def __init__(self) -> None:
        self._status: dict[str, JobStatus] = {}
        self._result: dict[str, str] = {}

    def create(self) -> str:
        job_id = str(uuid.uuid4())
        self._status[job_id] = JobStatus.PENDING
        return job_id

    def mark_running(self, job_id: str) -> None:
        self._status[job_id] = JobStatus.RUNNING

    def mark_done(self, job_id: str, result: str) -> None:
        self._status[job_id] = JobStatus.DONE
        self._result[job_id] = result

    def mark_failed(self, job_id: str) -> None:
        self._status[job_id] = JobStatus.FAILED

    def get_status(self, job_id: str) -> JobStatus:
        return self._status[job_id]

    def get_result(self, job_id: str) -> str | None:
        return self._result.get(job_id)


async def run_job(store: JobStore, job_id: str, *, should_fail: bool) -> None:
    store.mark_running(job_id)
    await asyncio.sleep(0.05)
    if should_fail:
        store.mark_failed(job_id)
    else:
        store.mark_done(job_id, "embedding vector computed")


async def main() -> None:
    store = JobStore()

    ok_job = store.create()
    print(f"{ok_job[:8]}: {store.get_status(ok_job).name}")  # PENDING

    await run_job(store, ok_job, should_fail=False)
    print(f"{ok_job[:8]}: {store.get_status(ok_job).name}, result={store.get_result(ok_job)}")

    failed_job = store.create()
    await run_job(store, failed_job, should_fail=True)
    print(f"{failed_job[:8]}: {store.get_status(failed_job).name}")


if __name__ == "__main__":
    asyncio.run(main())
