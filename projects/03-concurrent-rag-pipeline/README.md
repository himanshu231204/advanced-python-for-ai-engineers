# Project 03 — Concurrent RAG Pipeline

**Status:** ✅ Written

A retrieval pipeline that fans out to multiple retrieval sources concurrently, merges the
results, and feeds them to an LLM.

## Architecture

```text
Query
 ↓
parallel retrieval (each with its own per-branch timeout)
 ├── vector search
 ├── keyword search
 └── metadata filter
 ↓
merge + rerank (dedupe by text, keep the higher-scored copy, sort by score)
 ↓
LLM (mocked)
```

## Requirements

- Concurrent fan-out across retrieval sources with `asyncio.gather`
- Result merging and reranking step
- Timeout handling per retrieval branch
- Typed result models for each retrieval source

## Modules used

`12-concurrency`, `13-httpx-async-http`, `11-protocols-generics`, `09-pydantic`

## How it works

```text
answer_query(query)
      │
      ▼
asyncio.gather over three _run_branch_with_timeout(...) calls, one per source
      │           each wraps its branch in asyncio.wait_for(PER_BRANCH_TIMEOUT)
      │           a branch that times out returns [] instead of failing the whole query
      ▼
merge_and_rerank(branch_results): flatten, drop duplicate text (keep the
      higher score), sort by score, keep top_k
      ▼
generate(query, top_chunks) -- the mocked LLM call
      ▼
RagAnswer(query, used_chunks, answer)
```

`retrieval_sources.py` is deterministic and offline: each source matches against a small
fixed knowledge base by keyword overlap, so results are reproducible. The `metadata_filter`
source can be told to simulate a slow response, to demonstrate the pipeline surviving a
timed-out branch.

## Run it

```bash
pip install -r requirements.txt
python3 pipeline.py
```

Expected output:

```text
query: how do contextvars isolate async state?
  [vector score=0.9] Contextvars isolate per-task state under asyncio.
  [keyword score=0.6] threading.local breaks under asyncio because tasks share one thread.
answer: based on 2 source(s): Contextvars isolate per-task state under asyncio.

--- with the metadata branch timing out ---
[warn] metadata timed out -- continuing without it
  [vector score=0.9] Contextvars isolate per-task state under asyncio.
answer: based on 1 source(s): Contextvars isolate per-task state under asyncio.
```

## What this demonstrates

- Fanning out to independent retrieval sources concurrently with `asyncio.gather`, instead
  of querying them one after another
- Wrapping each branch in its own `asyncio.wait_for` so ONE slow source degrades the answer
  (fewer chunks) rather than blocking or failing the entire request
- A simple, typed merge/rerank step that treats every source's output uniformly via a shared
  `RetrievedChunk` model, regardless of which source produced it
- Keeping retrieval, merging, and generation as separate, independently testable functions

---

⬅ Back to [projects](../README.md)
