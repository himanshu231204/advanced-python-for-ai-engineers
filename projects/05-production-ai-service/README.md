# Project 05 — Production AI Service

**Status:** 🚧 Planned (not yet written)

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
`19-testing-pytest`, `27-production-python-patterns`

---

⬅ Back to [projects](../README.md)
