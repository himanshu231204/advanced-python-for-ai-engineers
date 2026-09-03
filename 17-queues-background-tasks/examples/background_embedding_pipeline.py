"""AI Engineering Example -- a FastAPI endpoint that accepts a document,
returns a job ID IMMEDIATELY (via BackgroundTasks), and processes the slow
embedding work in the background. A second endpoint polls the job's status
-- exactly the shape a real batch-embedding or long-running-agent API uses
so the client never blocks on a slow request.

Requires: fastapi, httpx (see requirements.txt)
Run: python3 background_embedding_pipeline.py
"""
from __future__ import annotations
import time
import uuid
from enum import Enum, auto
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()


class JobStatus(Enum):
    PENDING = auto()
    DONE = auto()


_status: dict[str, JobStatus] = {}
_result: dict[str, list[float]] = {}


def compute_embedding(job_id: str, text: str) -> None:
    time.sleep(0.05)  # pretend this is a slow embedding model call
    _result[job_id] = [float(len(word)) for word in text.split()]
    _status[job_id] = JobStatus.DONE


@app.post("/embed")
def submit_embedding(text: str, background_tasks: BackgroundTasks) -> dict[str, str]:
    job_id = str(uuid.uuid4())
    _status[job_id] = JobStatus.PENDING
    background_tasks.add_task(compute_embedding, job_id, text)
    return {"job_id": job_id}


@app.get("/embed/{job_id}")
def get_embedding(job_id: str) -> dict[str, object]:
    if job_id not in _status:
        raise HTTPException(status_code=404, detail="unknown job")
    status = _status[job_id]
    return {"status": status.name, "result": _result.get(job_id)}


if __name__ == "__main__":
    client = TestClient(app)

    submit_response = client.post("/embed", params={"text": "advanced python for ai"})
    job_id = submit_response.json()["job_id"]
    print("submitted:", job_id[:8])

    # TestClient waits for the background task to run before this call
    # returns, so the job is already DONE by the time we poll it here.
    status_response = client.get(f"/embed/{job_id}")
    print("status:", status_response.json())
