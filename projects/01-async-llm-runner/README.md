# Project 01 — Async LLM Runner

**Status:** 🚧 Planned (not yet written)

A concurrent runner that fires multiple LLM calls at once, safely.

## Requirements

- Async API calls to an LLM (or mock) endpoint
- Bounded concurrency (semaphore-limited fan-out)
- Retries with exponential backoff on transient failures
- Per-call timeout handling
- Structured (Pydantic) result objects
- Structured logging of successes/failures/timing

## Modules used

`03-asyncio`, `12-concurrency`, `15-error-handling-retries`, `20-logging-observability`, `09-pydantic`

---

⬅ Back to [projects](../README.md)
