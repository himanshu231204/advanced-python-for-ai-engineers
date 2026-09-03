# 12 — Concurrency

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

Fanning out dozens or hundreds of concurrent LLM/API calls safely requires more than `await`
-- you need gather, tasks, queues, semaphores, and timeouts. Module 03 covered *why*
`async`/`await` helps I/O-bound work; this module covers the actual toolkit for running many
of those awaits at once, safely, in production.

---

## 1. What is it?

A set of asyncio primitives for running multiple coroutines concurrently and controlling how
that concurrency behaves: `gather`/`as_completed` to wait for results, `Task`/`TaskGroup` to
schedule work independently, `Queue` to coordinate producers and consumers, `Semaphore` to cap
how much runs at once, and `timeout` to bound how long any single piece may take.

## 2. Why does it exist?

Calling one LLM API concurrently with `asyncio.gather` is easy (module 03). Calling *hundreds*
of them safely is a different problem: unbounded concurrency can exhaust connections or blow
through a provider's rate limit, a single hung request can stall an entire batch, and a single
failure shouldn't necessarily crash every other in-flight request. These primitives exist to
solve exactly those problems.

## 3. 💡 Mental Model

```text
asyncio.gather        -> "run these together, give me ALL results, in order"
asyncio.as_completed  -> "run these together, hand me each result AS IT FINISHES"
asyncio.Task          -> "start this now, independently, don't wait for an await"
asyncio.TaskGroup     -> "run these as one unit -- if one fails, cancel the rest"
asyncio.Queue         -> "a buffer between producers and worker consumers"
asyncio.Semaphore     -> "at most N of these may run at the same time"
asyncio.timeout       -> "give up on this specific await after N seconds"
```

## 4. Syntax

```python
import asyncio

# gather vs as_completed
results = await asyncio.gather(*coros)                 # ordered, waits for all
for coro in asyncio.as_completed(coros):
    result = await coro                                 # completion order

# Tasks / TaskGroup (3.11+)
task = asyncio.create_task(my_coro())                   # starts running immediately
async with asyncio.TaskGroup() as tg:
    tg.create_task(my_coro())                            # structured concurrency

# Queue
queue: asyncio.Queue[str] = asyncio.Queue()
await queue.put(item)
item = await queue.get()
queue.task_done()
await queue.join()                                        # wait until all items processed

# Semaphore -- concurrency limiting
sem = asyncio.Semaphore(10)
async with sem:
    await do_work()

# Timeout (3.11+)
async with asyncio.timeout(5):
    await slow_call()   # raises TimeoutError if it takes longer than 5s
```

## 5. Minimal Example

```python
import asyncio

async def fetch(n: int) -> int:
    await asyncio.sleep(0.1)
    return n * n

async def main() -> None:
    results = await asyncio.gather(*(fetch(i) for i in range(3)))
    print(results)  # [0, 1, 4]

asyncio.run(main())
```

## 6. What happens internally?

```text
asyncio.gather(fetch(1), fetch(2), fetch(3))
        │
        ▼
each coroutine is wrapped in a Task and scheduled on the event loop
        │
        ▼
the loop interleaves them: whichever task is ready to make progress
(not currently awaiting something) runs next
        │
        ▼
gather collects each Task's result as it finishes, but returns the full
list only once EVERY task has completed -- in the ORIGINAL argument order,
regardless of which one actually finished first
```

## 7. Comparison: asyncio vs Threading vs Multiprocessing

| | asyncio | Threading | Multiprocessing |
|---|---|---|---|
| Best for | I/O-bound (network, disk) | I/O-bound, esp. blocking libraries with no async API | CPU-bound work |
| Concurrency unit | coroutine (very cheap) | OS thread (moderate cost) | OS process (expensive) |
| Limited by the GIL? | n/a -- single thread | yes, for CPU-bound code | no -- separate interpreters |
| Typical count | thousands | tens to low hundreds | roughly # of CPU cores |
| AI use case | fanning out many concurrent API calls | wrapping a blocking SDK that has no async client | batch embedding/CPU-heavy preprocessing |

## 8. 🎯 AI Engineering Use Case

Real production LLM fan-out combines all three concerns: cap concurrency so you don't exceed
a rate limit, timeout each call so one hung request can't stall the batch, and collect
failures per-request instead of letting one bad response crash everything.

### Example A — Tiny

```python
results = await asyncio.gather(*(fetch(i) for i in range(3)))
```

### Example B — Practical

```python
sem = asyncio.Semaphore(10)
async def limited(coro):
    async with sem:
        return await coro
```

### Example C — AI Engineering

```python
async def safe_call(sem, prompt, *, per_call_timeout):
    async with sem:
        try:
            async with asyncio.timeout(per_call_timeout):
                return CallResult(prompt, await call_llm(prompt), None)
        except TimeoutError:
            return CallResult(prompt, None, "timed out")
        except Exception as e:
            return CallResult(prompt, None, str(e))
```

Full runnable version: [`examples/bounded_llm_fanout.py`](examples/bounded_llm_fanout.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
CONCURRENCY PRIMITIVES
✅ Good for:
- fanning out many independent I/O-bound calls (LLM, vector DB, search APIs)
- bounding how much concurrent work hits an external service (Semaphore)
- background job pipelines with multiple workers (Queue)

❌ Avoid when:
- the work is CPU-bound -- none of this helps (see module 03 §9, and use
  multiprocessing instead, module 25)
- there's only ever one or two calls to make -- plain sequential `await`
  is simpler and the added structure buys nothing

BETTER ALTERNATIVE
Use `multiprocessing` for CPU-bound batch work. Use plain sequential
`await` calls when there's no real concurrency to exploit.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — unbounded concurrent fan-out**

```python
# WRONG -- fires 10,000 requests at once with no limit, risking a rate-limit
# ban or exhausting connections/memory.
await asyncio.gather(*(call_llm(p) for p in ten_thousand_prompts))
```

```python
# BETTER -- cap concurrency with a semaphore
sem = asyncio.Semaphore(20)
async def limited(prompt):
    async with sem:
        return await call_llm(prompt)

await asyncio.gather(*(limited(p) for p in ten_thousand_prompts))
```

Runnable proof the semaphore actually caps concurrency:
[`examples/semaphore_and_timeout.py`](examples/semaphore_and_timeout.py)

**Mistake 2 — one failure crashing the entire batch**

```python
# WRONG -- asyncio.gather (default settings) re-raises the FIRST exception
# it sees, cancelling the rest of the batch and losing every other result.
results = await asyncio.gather(*(call_llm(p) for p in prompts))
```

```python
# BETTER -- catch errors per-call so one bad request doesn't sink the batch
async def safe_call(prompt):
    try:
        return await call_llm(prompt)
    except Exception as e:
        return None  # or a structured error result, see Example C above

results = await asyncio.gather(*(safe_call(p) for p in prompts))
```

**Mistake 3 — no timeout on individual calls**

```python
# WRONG -- one hung request blocks the whole gather() indefinitely,
# even though every OTHER call finished long ago.
await asyncio.gather(*(call_llm(p) for p in prompts))
```

```python
# BETTER
async def with_timeout(prompt):
    async with asyncio.timeout(5):
        return await call_llm(prompt)
```

Runnable proof: [`examples/semaphore_and_timeout.py`](examples/semaphore_and_timeout.py)

## 11. ⚡ Quick Tricks

```python
result = await asyncio.gather(...)
```

```python
# Structured concurrency: cancels sibling tasks automatically on failure
async with asyncio.TaskGroup() as tg:
    tg.create_task(coro_a())
    tg.create_task(coro_b())
```

```python
# Cap concurrency with a semaphore
sem = asyncio.Semaphore(10)
async with sem:
    ...
```

```python
# Bound any single await
async with asyncio.timeout(5):
    await slow_call()
```

## 12. Performance Considerations

- More concurrency isn't always faster -- past a certain point (the remote service's own
  capacity, or your own connection pool limits) extra concurrent requests just queue up or
  get rate-limited, adding latency rather than reducing it. Tune the semaphore limit based on
  the actual downstream service, not an arbitrary large number.
- `TaskGroup` and structured `except*` exception groups (3.11+) give cleaner cancellation
  semantics than manually tracking and cancelling a list of tasks yourself.

## 13. 🎤 Interview Questions

**Q: How would you limit 1000 concurrent API calls to at most 20 at a time?**
A: Wrap each call in `async with semaphore:` where `semaphore = asyncio.Semaphore(20)`, then
`asyncio.gather` all 1000 wrapped coroutines. The semaphore blocks the 21st coroutine's
`async with` block from proceeding until one of the first 20 releases its permit, so at most
20 calls are ever actually in flight.

**Q: What's the difference between `asyncio.gather` and `asyncio.as_completed`?**
A: `gather` waits for every coroutine and returns all results together, in the original
argument order. `as_completed` returns an iterator that yields each coroutine's result as
soon as it finishes, in completion order -- useful when you want to react to the fastest
result without waiting for the slowest.

**Q: Why prefer `asyncio.TaskGroup` over manually managing a list of tasks?**
A: `TaskGroup` provides structured concurrency: if any task in the group raises, the others
are automatically cancelled and the group itself raises an `ExceptionGroup` you can handle
with `except*`. Manually tracking tasks requires writing that cancellation and error-
aggregation logic yourself, and it's easy to leak a task that never gets cancelled.

**Q: What happens to the other 99 concurrent calls if one of 100 gathered coroutines raises
an exception, using default `asyncio.gather` settings?**
A: By default, `gather` immediately propagates the first exception it sees and cancels the
remaining tasks -- so you lose the results (or in-progress work) of every other call unless
you either catch exceptions inside each coroutine, or pass `return_exceptions=True` to have
`gather` return exceptions as regular result values instead of raising.

## 14. 🛠 Mini Exercise

Write `run_with_limit(coros: list[Coroutine], limit: int) -> list[object]` that runs the given
coroutines with at most `limit` running concurrently at any time, returning all results in
their original order (hint: wrap each coroutine so it acquires a shared semaphore before
running, then `asyncio.gather` the wrapped versions).

<details>
<summary>Solution</summary>

```python
import asyncio
from collections.abc import Coroutine
from typing import Any


async def run_with_limit(coros: list[Coroutine[Any, Any, Any]], limit: int) -> list[object]:
    sem = asyncio.Semaphore(limit)

    async def limited(coro: Coroutine[Any, Any, Any]) -> object:
        async with sem:
            return await coro

    return await asyncio.gather(*(limited(c) for c in coros))


async def fetch(n: int) -> int:
    await asyncio.sleep(0.05)
    return n * n


async def main() -> None:
    results = await run_with_limit([fetch(i) for i in range(5)], limit=2)
    print(results)  # [0, 1, 4, 9, 16]


asyncio.run(main())
```

</details>

## 15. Real-World Challenge

Extend [`examples/bounded_llm_fanout.py`](examples/bounded_llm_fanout.py) so `run_batch` also
accepts a `max_retries: int` and retries each failed (non-timeout) call up to that many times
before giving up -- combining this module's concurrency limiting with the retry pattern that
gets its own full treatment in `15-error-handling-retries`.

## 16. Cheat Sheet

```text
CONCURRENCY
↓

await asyncio.gather(*coros)              all results, original order, waits for all
for c in asyncio.as_completed(coros): ..  completion order, one at a time
asyncio.create_task(coro())               starts running immediately
async with asyncio.TaskGroup() as tg: ..  structured concurrency, auto-cancels siblings
async with asyncio.Semaphore(n): ...      caps concurrent work to n
async with asyncio.timeout(s): ...        bounds one await to s seconds

WHEN TO USE
-> fanning out many independent I/O-bound calls, safely bounded

COMMON MISTAKE
-> unbounded concurrent fan-out with no semaphore -> rate-limit bans, exhausted connections

AI USE CASE
-> semaphore + per-call timeout + per-call error handling around a batch of LLM calls
```

---

⬅ Back to [main README](../README.md)
