# Project 05 — Production AI Service

**Status:** ✅ Written

A small but production-shaped AI service, combining most of the Level 2/3 curriculum into
one deployable unit.

## Stack

```text
FastAPI
Pydantic
asyncio
HTTPX
logging
retry
caching
testing
configuration
```

## Requirements

- Config-driven setup (no hardcoded secrets/endpoints)
- Cached responses for repeated requests
- Retry + timeout handling on outbound calls
- Structured logging with request correlation IDs
- A pytest suite covering the core request path

## Modules used

`21-config-environments`, `16-caching`, `15-error-handling-retries`, `20-logging-observability`,
`19-testing-pytest`, `27-production-python-patterns`, `26-contextvars`

## How it works

```text
middleware: every request gets a fresh request_id, stored in a ContextVar
      │
      ▼
POST /summarize {"text": "..."}
      │
      ▼
cache.get(text)
      │
      ├── hit  -> log "cache_hit", return SummarizeResponse(cached=True)  -- no LLM call
      │
      └── miss -> log "cache_miss"
                     │
                     ▼
              summarize(text) -- asyncio.wait_for(provider_call, settings.llm_timeout_seconds),
                                  retried on timeout
                     │
                     ▼
              cache.set(text, result); return SummarizeResponse(cached=False)

GET /health/live   -> process responsive?
GET /health/ready  -> can it serve traffic?
```

- `config.py` loads one validated `Settings` object (via `pydantic-settings`) instead of
  scattering `os.environ` reads through the service.
- `cache.py` is a minimal TTL cache -- a repeated request within the TTL never re-triggers
  the (mocked, but in reality billed) LLM call.
- The correlation ID is stored in a `contextvars.ContextVar`, exactly the pattern from
  `26-contextvars` -- any code deep in the request's call chain can log the right
  `request_id` without it being threaded through every function signature.

## Run it

```bash
pip install -r requirements.txt

# start the real server
uvicorn app:app --reload

# or run the built-in offline demo
python3 app.py

# run the test suite
pytest tests/
```

Expected output of `python3 app.py` (the request IDs will differ each run):

```text
{'status': 'ok'}
{'status': 'ready'}
{"request_id": "9d9fcddb", "event": "cache_miss"}
{'summary': 'summary: contextvars isolate ', 'cached': False}
{"request_id": "683355fd", "event": "cache_hit"}
{'summary': 'summary: contextvars isolate ', 'cached': True}
```

`pytest tests/` runs 4 tests covering liveness, readiness, the cache-miss-then-hit path, and
request validation -- all pass.

## What this demonstrates

- Every piece of `27-production-python-patterns` in one real service: layering (config /
  cache / LLM client / route are separate modules), health checks, and config discipline
- A `ContextVar`-backed correlation ID attached to every log line for a request, without
  passing `request_id` through every function call
- Caching to avoid repeating an expensive outbound call for a request already answered
  recently
- A pytest suite exercising the actual FastAPI app via `TestClient`, including a validation
  failure case

---

⬅ Back to [projects](../README.md)
