# Project 02 — Streaming LLM API

**Status:** 🚧 Planned (not yet written)

A FastAPI service that streams LLM tokens to the client as they're generated.

## Stack

```text
FastAPI
HTTPX
async generator
SSE
Pydantic
```

## Requirements

- Async generator that yields tokens/events from an LLM (or mock) source
- FastAPI endpoint that streams the generator as Server-Sent Events
- Pydantic models for request validation and event payloads
- Graceful client-disconnect handling

## Modules used

`04-async-generators-streaming`, `14-streaming-sse-websockets`, `13-httpx-async-http`, `09-pydantic`

---

⬅ Back to [projects](../README.md)
