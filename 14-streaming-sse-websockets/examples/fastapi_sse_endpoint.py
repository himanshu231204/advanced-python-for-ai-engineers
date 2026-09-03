"""A FastAPI endpoint streaming Server-Sent Events from an async generator.
StreamingResponse is what turns "yield one chunk at a time" (module 04)
into an HTTP response the client receives incrementally, instead of
waiting for the whole body to be ready.

Requires: fastapi, httpx (see requirements.txt)
Run: python3 fastapi_sse_endpoint.py
"""
from __future__ import annotations
from collections.abc import AsyncIterator
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

app = FastAPI()


async def event_stream() -> AsyncIterator[str]:
    for i in range(3):
        await asyncio.sleep(0.01)
        yield f"data: tick {i}\n\n"


@app.get("/stream")
async def stream() -> StreamingResponse:
    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    # TestClient drives the app in-process -- no real server/port needed,
    # which is exactly why it's used for these runnable examples.
    client = TestClient(app)
    with client.stream("GET", "/stream") as response:
        for line in response.iter_lines():
            if line:
                print(line)
