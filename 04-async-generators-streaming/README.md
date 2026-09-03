# 04 — Async Generators & Streaming

**Level:** Level 1 | **Status:** 🚧 Planned (not yet written)

This is the exact pattern behind LLM token streaming: an async generator yielding tokens/events that FastAPI turns into a Server-Sent Events (SSE) response.

## What this module will cover

- Async iterators (`__aiter__` / `__anext__`)
- Async generator functions
- `async for`
- Streaming LLM tokens end-to-end
- Backpressure basics

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
