# 12 — Concurrency

**Level:** Level 3 | **Status:** 🚧 Planned (not yet written)

Fanning out dozens or hundreds of concurrent LLM/API calls safely requires more than `await` — you need gather, tasks, queues, semaphores, and timeouts.

## What this module will cover

- `asyncio.gather` vs `asyncio.as_completed`
- Tasks and task groups
- `asyncio.Queue`
- Semaphores for concurrency limiting
- Timeouts and cancellation
- asyncio vs threading vs multiprocessing

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
