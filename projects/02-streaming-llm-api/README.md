# Project 02 — Streaming LLM API

**Status:** ✅ Written

A FastAPI service that streams LLM tokens to the client as Server-Sent Events, as they're
generated, instead of buffering the whole response before replying.

## Stack

```text
FastAPI
HTTPX
async generator
SSE
Pydantic
```

## Requirements

- Async generator that yields tokens/events from an LLM (mocked here) source
- FastAPI endpoint that streams the generator as Server-Sent Events
- Pydantic models for request validation
- Graceful client-disconnect handling

## Modules used

`04-async-generators-streaming`, `14-streaming-sse-websockets`, `13-httpx-async-http`, `09-pydantic`

## How it works

```text
POST /generate/stream {"prompt": "..."}
      │
      ▼
GenerateRequest validates the body (Pydantic)
      │
      ▼
StreamingResponse(sse_event_stream(prompt, request))
      │
      ▼
sse_event_stream: async for token in stream_tokens(prompt):
      │
      ├── request.is_disconnected()? -> stop generating, don't waste work
      └── otherwise -> yield "data: {token, text_so_far}\n\n"   (one SSE event per token)
      │
      ▼
yield "data: [DONE]\n\n"   -- signals the client the stream is complete
```

`mock_llm.py` stands in for a real provider's streaming API -- it yields one word at a time
with a tiny delay, so this runs offline and deterministically.

## Run it

```bash
pip install -r requirements.txt

# start the real server
uvicorn app:app --reload
# then, in another terminal:
curl -N -X POST http://127.0.0.1:8000/generate/stream \
  -H "Content-Type: application/json" -d '{"prompt": "explain SSE"}'

# or run the built-in offline demo (uses FastAPI's TestClient, no server needed)
python3 app.py
```

Expected output of `python3 app.py`:

```text
received 7 token event(s)
final text: 'Here is a response to: explain SSE '
```

## What this demonstrates

- Streaming a response as it's generated, rather than buffering the full text and returning
  it all at once -- the same shape as a real LLM provider's streaming API
- Checking `request.is_disconnected()` inside the generator loop so an abandoned client
  connection stops the (potentially costly) generation early, instead of continuing to
  generate tokens no one will receive
- Validating the request body with a Pydantic model before any streaming begins
- Using `TestClient` to exercise a streaming endpoint offline, without a running server or
  real network I/O -- the same pattern used throughout `14-streaming-sse-websockets`

---

⬅ Back to [projects](../README.md)
