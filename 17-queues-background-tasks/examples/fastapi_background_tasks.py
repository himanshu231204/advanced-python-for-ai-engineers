"""FastAPI's BackgroundTasks: the response is sent to the client FIRST,
then the background function runs -- ideal for fire-and-forget work
(logging, sending a notification) that the client shouldn't have to wait on.

Requires: fastapi, httpx (see requirements.txt)
Run: python3 fastapi_background_tasks.py
"""
from __future__ import annotations
from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
_log: list[str] = []


def write_log(message: str) -> None:
    _log.append(message)  # runs AFTER the response has already been sent


@app.post("/submit")
def submit(text: str, background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(write_log, f"received: {text}")
    return {"status": "accepted"}


if __name__ == "__main__":
    client = TestClient(app)
    response = client.post("/submit", params={"text": "hello"})
    print("response:", response.json())
    print("log after request completed:", _log)
