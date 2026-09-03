"""AI Engineering Example -- the full pipeline from module 04's mental
model, now with the actual HTTP transport:

LLM -> tokens -> async generator -> FastAPI -> SSE -> Frontend

Requires: fastapi, httpx (see requirements.txt)
Run: python3 llm_token_sse_stream.py
"""
from __future__ import annotations
from collections.abc import AsyncIterator
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

app = FastAPI()

_FAKE_RESPONSE = "Server-Sent Events stream tokens as they are produced."


async def stream_llm_tokens(text: str) -> AsyncIterator[str]:
    """Same shape as 04-async-generators-streaming's stream_llm_tokens --
    the only new part is formatting each token as an SSE `data:` line."""
    for word in text.split(" "):
        await asyncio.sleep(0.01)
        yield f"data: {word}\n\n"


@app.get("/completion")
async def completion() -> StreamingResponse:
    return StreamingResponse(stream_llm_tokens(_FAKE_RESPONSE), media_type="text/event-stream")


def reconstruct_from_sse(raw_lines: list[str]) -> str:
    """What a frontend's EventSource handler effectively does: strip the
    `data: ` prefix from each event and reassemble the full text."""
    words = [line.removeprefix("data: ") for line in raw_lines if line.startswith("data: ")]
    return " ".join(words)


if __name__ == "__main__":
    client = TestClient(app)
    with client.stream("GET", "/completion") as response:
        lines = [line for line in response.iter_lines() if line]

    full_text = reconstruct_from_sse(lines)
    print(full_text)
    assert full_text == _FAKE_RESPONSE
