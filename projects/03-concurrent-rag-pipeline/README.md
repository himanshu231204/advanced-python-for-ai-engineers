# Project 03 — Concurrent RAG Pipeline

**Status:** 🚧 Planned (not yet written)

A retrieval pipeline that fans out to multiple retrieval sources concurrently, merges the
results, and feeds them to an LLM.

## Architecture

```text
Query
 ↓
parallel retrieval
 ├── vector search
 ├── keyword search
 ├── metadata filter
 └── reranker
 ↓
merge
 ↓
LLM
```

## Requirements

- Concurrent fan-out across retrieval sources with `asyncio.gather`
- Result merging and reranking step
- Timeout handling per retrieval branch
- Typed result models for each retrieval source

## Modules used

`12-concurrency`, `13-httpx-async-http`, `11-protocols-generics`, `09-pydantic`

---

⬅ Back to [projects](../README.md)
