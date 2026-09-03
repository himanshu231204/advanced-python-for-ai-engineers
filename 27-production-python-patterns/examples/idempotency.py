"""Idempotency -- a client retrying a request after a timeout (it never
saw the response, but the server may have already processed it) must not
cause the side effect to happen twice. An idempotency key lets the server
recognize "I've already done this" and return the original result instead
of repeating the work.

Run: python3 idempotency.py
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class JobResult:
    job_id: str
    status: str


class JobSubmitter:
    def __init__(self) -> None:
        self._seen: dict[str, JobResult] = {}
        self._next_id = 1

    def submit(self, idempotency_key: str, payload: str) -> JobResult:
        if idempotency_key in self._seen:
            return self._seen[idempotency_key]  # replay -- no new work done

        job_id = f"job-{self._next_id}"
        self._next_id += 1
        result = JobResult(job_id=job_id, status=f"submitted: {payload}")
        self._seen[idempotency_key] = result
        return result


if __name__ == "__main__":
    submitter = JobSubmitter()

    first = submitter.submit("req-abc", "embed document 42")
    print(first)  # job-1

    # Client's connection dropped after this; it retries with the SAME key.
    retried = submitter.submit("req-abc", "embed document 42")
    print(retried)  # SAME job-1 -- not job-2, no duplicate work

    different = submitter.submit("req-xyz", "embed document 43")
    print(different)  # job-2 -- a genuinely different request
