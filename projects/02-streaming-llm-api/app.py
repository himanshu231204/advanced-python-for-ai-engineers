"""Streaming LLM API -- a FastAPI service that streams LLM tokens to the
client as Server-Sent Events, as they're generated, instead of buffering
the full response before replying.

Combines: async generators (04), FastAPI streaming/SSE (14),
HTTPX (13, exercised by the test client), Pydantic (09).

Run the server:  uvicorn app:app --reload
Run the demo:    python3 app.py
"""
from __future__ import annotations
import json

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

from mock_llm import stream_tokens

app = FastAPI()


class GenerateRequest(BaseModel):
    prompt: str


async def sse_event_stream(prompt: str, request: Request):
    """Formats each token as an SSE `data:` line, and stops early if the
    client disconnects instead of continuing to generate for no one."""
    full_text = ""
    async for token in stream_tokens(prompt):
        if await request.is_disconnected():
            break  # graceful client-disconnect handling
        full_text += token
        yield f"data: {json.dumps({'token': token, 'text_so_far': full_text})}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/generate/stream")
async def generate_stream(payload: GenerateRequest, request: Request) -> StreamingResponse:
    return StreamingResponse(
        sse_event_stream(payload.prompt, request), media_type="text/event-stream"
    )


def _parse_sse_events(raw_body: str) -> list[dict[str, str]]:
    events = []
    for line in raw_body.splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            events.append(json.loads(line.removeprefix("data: ")))
    return events


if __name__ == "__main__":
    client = TestClient(app)
    response = client.post("/generate/stream", json={"prompt": "explain SSE"})
    events = _parse_sse_events(response.text)

    print(f"received {len(events)} token event(s)")
    print(f"final text: {events[-1]['text_so_far']!r}")
