# 17 — Queues & Background Tasks

**Level:** Level 3 | **Status:** 🚧 Planned (not yet written)

Long-running AI jobs (batch embedding, evaluation runs, agent workflows) belong in background workers, not in the request/response cycle.

## What this module will cover

- Producer/consumer pattern
- `asyncio.Queue` for background work
- FastAPI `BackgroundTasks`
- Bounded vs unbounded queues

## Structure (once written)

Each topic in this module follows the repository's standard template — see
[`AGENTS.md`](../AGENTS.md#topic-template) for the full section list:

```text
Concept -> Mental Model -> Why it exists -> Syntax -> Minimal Example
-> Internal Working -> AI Engineering Use Case -> Common Mistakes
-> Quick Tricks -> When to Use / When Not To -> Interview Questions
-> Mini Exercises -> Runnable Code -> Cheat Sheet
```

---

⬅ Back to [main README](../README.md)
