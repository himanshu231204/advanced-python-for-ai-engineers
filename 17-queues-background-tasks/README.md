# 17 — Queues & Background Tasks

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

Long-running AI jobs (batch embedding, evaluation runs, agent workflows) belong in background
workers, not in the request/response cycle. Module 12 introduced `asyncio.Queue` as a
concurrency primitive; this module is about the application pattern built on top of it --
keeping slow work off the critical path of a user-facing request.

> Examples in this module need `fastapi` and `httpx`. See [`requirements.txt`](requirements.txt).

---

## 1. What is it?

A background task is work scheduled to run *after* (or independently of) the response a
client is waiting on. A queue is the buffer between something that produces work (a request
handler) and something that consumes it (one or more background workers), decoupling how fast
work arrives from how fast it gets processed.

## 2. Why does it exist?

A user submitting a document for embedding, or kicking off a multi-step agent evaluation run,
shouldn't have to keep an HTTP connection open for however long that takes. Queues and
background tasks let the request return immediately (often with a job ID), while the actual
slow work happens separately -- checked on later, or fired-and-forgotten entirely.

## 3. 💡 Mental Model

```text
request handler
      │
      ▼
enqueue job / schedule background task  -> respond to the client IMMEDIATELY
      │
      ▼
(separately, off the request path)
worker(s) pull from the queue, do the slow work, record the result/status
```

## 4. Syntax

```python
# FastAPI BackgroundTasks -- runs AFTER the response is sent
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

@app.post("/submit")
def submit(text: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(process, text)
    return {"status": "accepted"}   # client gets this immediately

# asyncio.Queue -- a shared buffer between producer(s) and worker(s)
queue: asyncio.Queue[Job] = asyncio.Queue()          # unbounded
queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=100)  # bounded -- backpressure

await queue.put(job)
job = await queue.get()
queue.task_done()
await queue.join()   # wait until every enqueued item has been processed
```

## 5. Minimal Example

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def log_it(message: str) -> None:
    print(f"logged: {message}")

@app.post("/ping")
def ping(background_tasks: BackgroundTasks):
    background_tasks.add_task(log_it, "someone pinged")
    return {"ok": True}
```

## 6. What happens internally?

```text
@app.post("/submit")
def submit(text, background_tasks):
    background_tasks.add_task(process, text)
    return {"status": "accepted"}
        │
        ▼
FastAPI/Starlette builds the HTTP response from the return value
        │
        ▼
the response is SENT to the client
        │
        ▼
only THEN does Starlette actually call process(text) -- the client
already has its answer and isn't waiting on this
```

## 7. Comparison: FastAPI BackgroundTasks vs asyncio.Queue Worker Pool

| | `BackgroundTasks` | `asyncio.Queue` + workers |
|---|---|---|
| Scope | one task, tied to one request's lifecycle | a persistent pool processing many jobs over time |
| Concurrency control | none built-in -- runs after that response | you control worker count, so concurrency is bounded |
| Survives past the request? | no -- runs once, per request | yes -- workers keep running, pulling from the shared queue |
| Best for | quick fire-and-forget work (logging, a notification) | sustained background job processing (batch embedding, an evaluation queue) |

## 8. 🎯 AI Engineering Use Case

Accepting a document for embedding, returning a job ID immediately, and letting the client
poll for the result is the standard shape for any slow AI operation that shouldn't block the
request.

### Example A — Tiny

```python
@app.post("/ping")
def ping(background_tasks: BackgroundTasks):
    background_tasks.add_task(log_it, "pinged")
    return {"ok": True}
```

### Example B — Practical

```python
async def worker(queue: asyncio.Queue[Job]) -> None:
    while True:
        job = await queue.get()
        await process_job(job)
        queue.task_done()
```

### Example C — AI Engineering

```python
@app.post("/embed")
def submit_embedding(text: str, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    status[job_id] = JobStatus.PENDING
    background_tasks.add_task(compute_embedding, job_id, text)
    return {"job_id": job_id}

@app.get("/embed/{job_id}")
def get_embedding(job_id: str):
    return {"status": status[job_id].name, "result": result.get(job_id)}
```

Full runnable version: [`examples/background_embedding_pipeline.py`](examples/background_embedding_pipeline.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
BACKGROUND TASKS & QUEUES
✅ Good for:
- work that takes too long to hold an HTTP connection open for
- fire-and-forget side effects (logging, notifications) after a response
- sustained job processing with controlled concurrency (a worker pool)

❌ Avoid when:
- the client genuinely needs the result before it can proceed (just await
  it directly in the request handler instead)
- a single process's BackgroundTasks isn't durable enough for your needs
  (a crash loses in-flight background tasks -- see the note below)

BETTER ALTERNATIVE
For work that MUST survive a process restart, or needs to be distributed
across multiple machines, use a real task queue (Celery, RQ, or a managed
queue service) instead of in-process BackgroundTasks/asyncio.Queue.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — an unbounded queue with no backpressure**

```python
# WRONG -- if the producer is faster than the workers, this queue grows
# without limit, risking unbounded memory use under sustained load.
queue: asyncio.Queue[Job] = asyncio.Queue()
```

```python
# BETTER -- a bounded queue makes put() await once full, naturally
# slowing the producer down to the workers' actual processing rate.
queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=1000)
```

Runnable proof of the size difference: [`examples/bounded_vs_unbounded_queue.py`](examples/bounded_vs_unbounded_queue.py)

**Mistake 2 — assuming `BackgroundTasks` survives a process crash/restart**

```python
# WRONG ASSUMPTION -- if the process crashes after responding but before
# the background task runs, that work is simply lost -- there's no
# persistence or retry built in.
background_tasks.add_task(charge_customer, order_id)
```

```python
# BETTER -- for anything that must not be silently lost, use a durable
# task queue (with its own persistence and retry) instead of in-process
# BackgroundTasks.
```

**Mistake 3 — no way to check a background job's status**

```python
# WRONG -- fire-and-forget with zero tracking means the client (and you,
# debugging) has no way to know if the job succeeded, failed, or is
# still running.
background_tasks.add_task(process_document, doc_id)
return {"status": "accepted"}  # ...and then what?
```

```python
# BETTER -- record status per job ID so it can be polled
job_id = create_job()
background_tasks.add_task(process_document, job_id, doc_id)
return {"job_id": job_id}
```

Runnable proof: [`examples/job_status_tracking.py`](examples/job_status_tracking.py)

## 11. ⚡ Quick Tricks

```python
# Fire-and-forget after a response
background_tasks.add_task(fn, *args)
```

```python
# Bound a queue to apply natural backpressure
queue = asyncio.Queue(maxsize=1000)
```

```python
# Cleanly stop a worker pool with a sentinel value
await queue.put(None)  # each worker treats None as "stop"
```

```python
# Wait until every enqueued item has actually been processed
await queue.join()
```

## 12. Performance Considerations

- More workers isn't always better -- past the point where downstream resources (a DB, an
  embedding model, an external API) are saturated, extra workers just add contention rather
  than throughput.
- A bounded queue trades a small amount of producer latency (waiting for room) for a hard cap
  on memory use -- almost always worth it for any queue accepting external, unpredictable
  load.

## 13. 🎤 Interview Questions

**Q: When would you use FastAPI's `BackgroundTasks` instead of a full task queue?**
A: For quick, low-stakes work tied to a single request's lifecycle -- logging, sending a
notification -- where losing the task on a crash is an acceptable risk and no cross-process
coordination is needed. Anything that must survive a restart, be retried reliably, or run on
a different machine than the web server needs a real task queue instead.

**Q: Why use a bounded queue instead of an unbounded one for background job processing?**
A: An unbounded queue lets a producer that's faster than the consumers pile up unlimited
in-memory work, risking out-of-memory failures under sustained load. A bounded queue makes
`put()` block (apply backpressure) once full, capping memory use at the cost of slowing the
producer down to match actual processing capacity.

**Q: How would you let a client check on a long-running background job's progress?**
A: Generate a job ID when the job is submitted, store its status (pending/running/done/
failed) and eventual result keyed by that ID, and expose a separate endpoint the client can
poll with the job ID to retrieve the current status -- exactly the submit/poll pattern used
for batch embedding or long-running agent runs.

**Q: What's the risk of relying only on in-process `BackgroundTasks` for critical work?**
A: If the process crashes or restarts after the response is sent but before the background
task finishes (or even starts), that work is silently lost -- there's no persistence, retry,
or cross-process visibility. Critical work needs a durable task queue that survives process
restarts.

## 14. 🛠 Mini Exercise

Write an async function `run_worker_pool(jobs: list[str], *, num_workers: int, process) ->
list[str]` that processes each job string through the given async `process` function using a
pool of `num_workers` workers pulling from a shared `asyncio.Queue`, returning all results
(order doesn't need to be preserved).

<details>
<summary>Solution</summary>

```python
import asyncio
from collections.abc import Awaitable, Callable


async def run_worker_pool(
    jobs: list[str], *, num_workers: int, process: Callable[[str], Awaitable[str]]
) -> list[str]:
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    results: list[str] = []

    async def worker() -> None:
        while True:
            job = await queue.get()
            if job is None:
                queue.task_done()
                break
            results.append(await process(job))
            queue.task_done()

    workers = [asyncio.create_task(worker()) for _ in range(num_workers)]
    for job in jobs:
        await queue.put(job)
    for _ in workers:
        await queue.put(None)

    await asyncio.gather(*workers)
    return results


async def double(s: str) -> str:
    await asyncio.sleep(0.01)
    return s + s


async def main() -> None:
    results = await run_worker_pool(["a", "b", "c"], num_workers=2, process=double)
    print(sorted(results))  # ['aa', 'bb', 'cc']


asyncio.run(main())
```

</details>

## 15. Real-World Challenge

Extend [`examples/background_embedding_pipeline.py`](examples/background_embedding_pipeline.py)
so `compute_embedding` can fail (simulate it for some inputs), setting the job's status to a
new `FAILED` state with an error message, and have `GET /embed/{job_id}` return that error
instead of a `result` when the job failed -- practice surfacing background failures through
the same polling interface used for success.

## 16. Cheat Sheet

```text
QUEUES & BACKGROUND TASKS
↓

background_tasks.add_task(fn, *args)        fire-and-forget, after the response

queue = asyncio.Queue(maxsize=N)            bounded -- backpressure
await queue.put(item) / await queue.get()   producer / consumer
queue.task_done() / await queue.join()      mark done / wait for full drain

WHEN TO USE
-> slow work that shouldn't block a request; sustained job processing with a worker pool

COMMON MISTAKE
-> an unbounded queue with no backpressure -> unlimited memory growth under load

AI USE CASE
-> submit a document for embedding, return a job ID immediately, poll for the result
```

---

⬅ Back to [main README](../README.md)
