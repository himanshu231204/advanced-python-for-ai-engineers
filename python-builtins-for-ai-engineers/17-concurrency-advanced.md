# 17 — Concurrency (Advanced)

Context propagation across async boundaries and garbage collection tuning — advanced concurrency control for production AI services.

---

## `contextvars`

**Import:** `from contextvars import ContextVar, copy_context`

**When to use:** Propagate request_id, user_id, or trace_id across async agent coroutines without passing them through every function signature.

**Mental model:** A clipboard that follows each async task independently — even when coroutines interleave on the same event loop, each one sees its own clipboard values without cross-contamination.

```python
from contextvars import ContextVar
import asyncio
import logging

request_id: ContextVar[str] = ContextVar("request_id", default="no-request")
user_id: ContextVar[str] = ContextVar("user_id", default="anonymous")

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger("agent")

def log(msg: str) -> None:
    """Log with automatic request context — no need to pass IDs around."""
    logger.info(f"[{request_id.get()}] [{user_id.get()}] {msg}")

async def call_llm(prompt: str) -> str:
    log(f"Calling LLM with: {prompt[:30]}...")
    await asyncio.sleep(0.1)
    log("LLM response received")
    return f"Answer to: {prompt}"

async def call_tool(name: str) -> str:
    log(f"Running tool: {name}")
    await asyncio.sleep(0.05)
    return f"{name}: result"

async def handle_request(req_id: str, uid: str, query: str) -> str:
    """Each request gets its own context — no cross-contamination."""
    request_id.set(req_id)
    user_id.set(uid)
    log(f"Processing query: {query}")

    llm_result, tool_result = await asyncio.gather(
        call_llm(query),
        call_tool("web_search"),
    )
    log("Request complete")
    return f"{llm_result} | {tool_result}"

async def main() -> None:
    results = await asyncio.gather(
        handle_request("req-001", "user-alice", "What is RAG?"),
        handle_request("req-002", "user-bob", "Explain embeddings"),
    )
    for r in results:
        print(r)

asyncio.run(main())
```

**Gotcha:** `ContextVar` values are scoped to the current task. `asyncio.create_task()` automatically copies the context, but `threading.Thread()` does not — use `copy_context().run()` for threads.

---

## `gc`

**Import:** `import gc`

**When to use:** Debug memory leaks in long-running agent services, tune GC for latency-sensitive inference endpoints, track circular references.

**Mental model:** The janitor for Python's memory — it finds and cleans up circular references that regular reference counting can't handle. In latency-sensitive code, you can tell the janitor when (not) to clean.

```python
import gc
import sys

def debug_memory_leaks() -> dict[str, int]:
    """Identify potential memory leaks in a long-running agent process."""
    gc.collect()
    stats = gc.get_stats()

    report = {
        "gen0_collections": stats[0]["collections"],
        "gen1_collections": stats[1]["collections"],
        "gen2_collections": stats[2]["collections"],
        "uncollectable": stats[2]["uncollectable"],
        "tracked_objects": len(gc.get_objects()),
    }

    # Find objects that survived multiple GC generations (potential leaks)
    gc.collect()
    old_objects = gc.get_objects()
    large_objects = [
        (type(obj).__name__, sys.getsizeof(obj))
        for obj in old_objects
        if sys.getsizeof(obj) > 10_000
    ]
    report["large_objects_count"] = len(large_objects)
    return report

class LatencyOptimizedServer:
    """Disable GC during inference for consistent latency, collect between requests."""
    def __init__(self) -> None:
        gc.disable()
        self._request_count = 0

    def handle_request(self, query: str) -> str:
        self._request_count += 1
        result = f"Response to: {query}"

        # Collect garbage between requests, not during
        if self._request_count % 100 == 0:
            collected = gc.collect()
            if collected > 50:
                print(f"GC collected {collected} objects after {self._request_count} requests")

        return result

report = debug_memory_leaks()
print(f"Tracked objects: {report['tracked_objects']}")
print(f"Large objects: {report['large_objects_count']}")
```

**Gotcha:** `gc.disable()` stops only the cyclic GC — reference counting still works. Disable GC only when you understand your allocation patterns; leaking circular references without GC will slowly eat all your memory.
