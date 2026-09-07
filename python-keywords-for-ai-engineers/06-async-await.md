# 06 — Async & Await

The two keywords that make Python's concurrency model work — the backbone of every production AI backend that calls LLMs, tools, and vector databases concurrently.

---

## `async`

**Syntax:** `async def name():` / `async for` / `async with` (mark a function, loop, or context manager as asynchronous)

**When to use:** Define coroutines for concurrent I/O — LLM API calls, parallel tool execution, streaming responses, concurrent embedding requests, async database queries.

**Mental model:** The "multitasking" badge — putting `async` on a function says "this function may need to wait for things (network, disk, APIs), and while it waits, other tasks can run." The function becomes a coroutine that must be `await`ed.

```python
import asyncio
from typing import Any

async def call_llm(prompt: str, model: str = "claude-3") -> dict[str, Any]:
    """Simulate an async LLM API call."""
    await asyncio.sleep(0.1)  # Simulates network latency
    return {"content": f"[{model}] Answer to: {prompt[:30]}", "tokens": 42}

async def call_tool(name: str, args: dict[str, str]) -> str:
    """Simulate an async tool call."""
    await asyncio.sleep(0.05)
    return f"{name}({args}) -> result"

async def agent_step(query: str) -> dict[str, Any]:
    """Run LLM call and tool calls concurrently."""
    llm_task = call_llm(query)
    tool_task = call_tool("search", {"q": query})

    # Both run concurrently — total time is max(0.1, 0.05), not 0.15
    llm_result, tool_result = await asyncio.gather(llm_task, tool_task)
    return {"llm": llm_result, "tool": tool_result}

# async for — iterate over an async stream
async def token_stream(text: str):
    """Simulate streaming tokens from an LLM."""
    for word in text.split():
        await asyncio.sleep(0.01)
        yield word

async def main() -> None:
    # Concurrent agent step
    result = await agent_step("What is RAG?")
    print(f"LLM: {result['llm']['content']}")
    print(f"Tool: {result['tool']}")

    # Async iteration over a stream
    tokens: list[str] = []
    async for token in token_stream("RAG combines retrieval with generation"):
        tokens.append(token)
    print(f"Streamed {len(tokens)} tokens: {' '.join(tokens)}")

asyncio.run(main())
```

**Gotcha:** An `async def` function returns a coroutine object, not the result — you must `await` it or schedule it with `asyncio.create_task()`. Calling `call_llm("hi")` without `await` does nothing and silently discards the work. Python will emit a "coroutine was never awaited" warning, but only at garbage collection time.

---

## `await`

**Syntax:** `result = await coroutine` (suspend until the coroutine completes)

**When to use:** Every point where you need the result of an async operation — waiting for LLM responses, database queries, HTTP requests, tool execution results.

**Mental model:** The "take a number and wait" counter — `await` says "I need this result before I can continue, but while I'm waiting, other customers (coroutines) can be served." The event loop switches to other ready tasks and comes back when your result arrives.

```python
import asyncio
import time
from typing import Any

async def embed_text(text: str) -> list[float]:
    """Simulate an async embedding API call."""
    await asyncio.sleep(0.05)
    return [0.1 * (i % 10) for i in range(len(text))][:8]

async def search_vectors(embedding: list[float], top_k: int = 3) -> list[dict[str, Any]]:
    """Simulate async vector database search."""
    await asyncio.sleep(0.03)
    return [{"id": i, "score": 0.9 - i * 0.1} for i in range(top_k)]

async def rag_pipeline(query: str) -> str:
    """A full RAG pipeline showing sequential and parallel await patterns."""
    # Sequential: embed must finish before search can start
    embedding = await embed_text(query)
    results = await search_vectors(embedding)

    # Parallel: fetch all document contents concurrently
    async def fetch_doc(doc_id: int) -> str:
        await asyncio.sleep(0.02)
        return f"Document {doc_id} content..."

    doc_tasks = [fetch_doc(r["id"]) for r in results]
    docs = await asyncio.gather(*doc_tasks)

    return f"Found {len(docs)} docs for: {query}"

async def main() -> None:
    start = time.perf_counter()

    # Parallel: run multiple independent RAG queries concurrently
    queries = ["What is RAG?", "Explain embeddings", "Define HNSW"]
    results = await asyncio.gather(*[rag_pipeline(q) for q in queries])

    elapsed = time.perf_counter() - start
    for r in results:
        print(f"  {r}")
    print(f"3 queries completed in {elapsed:.2f}s (concurrent, not 3x serial)")

asyncio.run(main())
```

**Gotcha:** You can only use `await` inside an `async def` function — using it in a regular function is a `SyntaxError`. Also, `await` only works with awaitables (coroutines, tasks, futures) — you can't `await` a regular function call. If you need to call sync code from async, use `asyncio.to_thread()` to avoid blocking the event loop.
