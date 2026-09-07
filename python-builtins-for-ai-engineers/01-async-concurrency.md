# 01 — Async & Concurrency

Python's concurrency toolkit for AI engineers — from cooperative I/O to true parallelism.

---

## `asyncio`

**Import:** `import asyncio`

**When to use:** Fan out multiple LLM/tool/retrieval calls concurrently in an async agent loop.

**Mental model:** Traffic controller — it doesn't run things in parallel, it switches between tasks when one is waiting (I/O). Think: a waiter serving multiple tables, not multiple waiters.

```python
import asyncio
from typing import Any

async def call_llm(prompt: str) -> dict[str, Any]:
    await asyncio.sleep(0.3)  # simulates network I/O to LLM API
    return {"role": "assistant", "content": f"Answer to: {prompt}"}

async def call_tool(name: str) -> str:
    await asyncio.sleep(0.2)
    return f"{name}: result_data"

async def agent_step(query: str) -> dict[str, Any]:
    llm_task = asyncio.create_task(call_llm(query))
    tool_tasks = [asyncio.create_task(call_tool(t)) for t in ["search", "calculator"]]
    llm_response = await llm_task
    tool_results = await asyncio.gather(*tool_tasks)
    return {"llm": llm_response, "tools": tool_results}

asyncio.run(agent_step("What is 2+2?"))
```

**Gotcha:** Calling `asyncio.run()` inside an already-running loop raises `RuntimeError`. In notebooks use `await` directly; in nested contexts use `asyncio.create_task()`.

---

## `concurrent.futures`

**Import:** `from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor`

**When to use:** Run blocking SDK calls (OpenAI sync client, database drivers) without freezing your async event loop.

**Mental model:** A temp agency — you hand off blocking jobs to a pool of workers and collect results when they're done, while your main thread stays responsive.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

def sync_embedding_call(text: str) -> list[float]:
    """Blocking SDK call that can't be awaited."""
    import time; time.sleep(0.1)
    return [0.1, 0.2, 0.3]  # simulated embedding vector

async def get_embeddings(texts: list[str]) -> list[list[float]]:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [
            loop.run_in_executor(pool, sync_embedding_call, text)
            for text in texts
        ]
        return await asyncio.gather(*futures)

results = asyncio.run(get_embeddings(["hello", "world", "test"]))
print(f"Got {len(results)} embeddings, dim={len(results[0])}")
```

**Gotcha:** `ProcessPoolExecutor` pickles arguments across process boundaries — lambdas, closures, and unpicklable objects will fail silently or raise.

---

## `threading`

**Import:** `import threading`

**When to use:** Background token streaming to a UI while main thread processes tool calls.

**Mental model:** Multiple cashiers sharing one register key (the GIL) — only one can ring up at a time, but while one waits for a card reader (I/O), another can jump in.

```python
import threading
import queue
import time

token_queue: queue.Queue[str | None] = queue.Queue()

def stream_tokens() -> None:
    """Simulates LLM streaming tokens into a shared queue."""
    for token in ["Hello", " world", "!", None]:
        time.sleep(0.05)
        token_queue.put(token)

def render_ui() -> None:
    """Consumes tokens and renders them as they arrive."""
    while True:
        token = token_queue.get()
        if token is None:
            break
        print(token, end="", flush=True)
    print()

producer = threading.Thread(target=stream_tokens)
consumer = threading.Thread(target=render_ui)
producer.start()
consumer.start()
producer.join()
consumer.join()
```

**Gotcha:** Threads share memory — mutating a shared `list` or `dict` without a `Lock` causes subtle race conditions that surface only under load.

---

## `multiprocessing`

**Import:** `from multiprocessing import Pool`

**When to use:** CPU-heavy batch jobs — chunked embedding generation, large-scale text preprocessing, FAISS index building.

**Mental model:** Multiple kitchens, each with its own chef and stove — true parallelism with no GIL, but passing ingredients between kitchens (serialization) costs time.

```python
from multiprocessing import Pool
import math

def compute_chunk_similarity(chunk_pair: tuple[list[float], list[float]]) -> float:
    """CPU-bound cosine similarity between two embedding vectors."""
    a, b = chunk_pair
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

if __name__ == "__main__":
    pairs = [([0.1, 0.2, 0.3], [0.4, 0.5, 0.6])] * 10_000
    with Pool(processes=4) as pool:
        similarities = pool.map(compute_chunk_similarity, pairs)
    print(f"Computed {len(similarities)} similarities")
```

**Gotcha:** Always guard with `if __name__ == "__main__"` — without it, worker processes re-import the module and spawn infinite subprocesses on some platforms.

---

## `queue`

**Import:** `from queue import Queue, PriorityQueue`

**When to use:** Thread-safe pipeline between producer (LLM stream) and consumer (persistence/UI) in a multi-threaded agent.

**Mental model:** A conveyor belt with bumpers — producers drop items on one end, consumers pick them up on the other, and the belt itself handles all the synchronization.

```python
from queue import PriorityQueue
from dataclasses import dataclass, field

@dataclass(order=True)
class AgentTask:
    priority: int
    description: str = field(compare=False)
    tool: str = field(compare=False)

task_queue: PriorityQueue[AgentTask] = PriorityQueue()

task_queue.put(AgentTask(priority=3, description="Log metrics", tool="logger"))
task_queue.put(AgentTask(priority=1, description="Answer user", tool="llm"))
task_queue.put(AgentTask(priority=2, description="Fetch context", tool="retriever"))

while not task_queue.empty():
    task = task_queue.get()
    print(f"[P{task.priority}] {task.description} → {task.tool}")
    # [P1] Answer user → llm
    # [P2] Fetch context → retriever
    # [P3] Log metrics → logger
```

**Gotcha:** `queue.Queue` is for threads only. In async code use `asyncio.Queue`; in multiprocessing use `multiprocessing.Queue`.
