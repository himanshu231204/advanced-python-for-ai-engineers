# 03 — Asyncio Fundamentals

**Level:** 1 (Modern Python Core) | **Status:** ✅ Written

`async`/`await` is the backbone of every modern AI backend. LLM calls, vector DB lookups,
search APIs, and tool calls are all **I/O-bound** -- most of their time is spent waiting on a
network response, not computing -- and asyncio lets Python do useful work while it waits
instead of sitting idle.

This module covers the fundamentals only: coroutines, the event loop, and why this matters.
Fan-out patterns like `asyncio.gather` with semaphores/timeouts/task groups are covered in
depth in `12-concurrency` -- here they're used just enough to demonstrate the core idea.

---

## 1. What is it?

`async def` defines a **coroutine function**. Calling it doesn't run the function -- it
creates a **coroutine object**, a paused computation that only executes when something
`await`s it or an event loop runs it. `await` hands control back to the event loop while
waiting on something (I/O, a timer, another coroutine), letting the loop run other work in
the meantime.

## 2. Why does it exist?

A typical AI request touches multiple slow, independent I/O operations:

```text
LLM application
 ├── LLM API           (network wait)
 ├── Search API         (network wait)
 ├── Vector DB           (network wait)
 ├── SQL DB                (network wait)
 └── Tool calls              (network wait)
```

Threads can do this too, but each OS thread is comparatively expensive (megabytes of stack,
kernel-level context switches). Coroutines are cheap, single-threaded, and cooperatively
scheduled -- thousands of them can be "in flight" waiting on I/O with very little overhead.

## 3. 💡 Mental Model

```text
Coroutine
   ↓
Task                (a coroutine scheduled to run on the event loop)
   ↓
Event Loop
   ↓
I/O operation        (network call, timer, ...)
   ↓
Other task runs       (the loop picks up whatever ISN'T waiting)
   ↓
I/O completes
   ↓
Coroutine resumes     (exactly where it left off, after the `await`)
```

Think of the event loop as a single chef who never stands idle: while one dish simmers
(waiting on I/O), the chef starts prepping the next one, instead of just watching the pot.

## 4. Syntax

```python
import asyncio

async def fetch(name: str) -> str:
    await asyncio.sleep(0.5)   # stand-in for a real network wait
    return f"{name} done"

async def main() -> None:
    result = await fetch("llm-call")   # await = "run this, and give me its result"
    print(result)

asyncio.run(main())   # the standard entry point for a top-level async program
```

## 5. Minimal Example

```python
import asyncio

async def greet(name: str) -> str:
    await asyncio.sleep(0.1)
    return f"Hello, {name}!"

async def main() -> None:
    print(await greet("world"))

asyncio.run(main())  # Hello, world!
```

## 6. What happens internally?

```text
coro = fetch("llm-call")
        │
        ▼
Nothing runs yet -- `coro` is just a coroutine object (compare to a generator
object from module 02: creating it doesn't execute the body)
        │
        ▼
await coro   (inside a running event loop)
        │
        ▼
Function body starts executing synchronously...
        │
        ▼
hits `await asyncio.sleep(0.5)`
        │
        ▼
control returns to the event loop; loop runs OTHER ready tasks
        │
        ▼
after 0.5s, the loop resumes this coroutine right after the `await`
        │
        ▼
function returns its value -> that becomes the result of `await coro`
```

## 7. Comparison: Sync vs Async

| | Synchronous | Asynchronous (`async`/`await`) |
|---|---|---|
| Model | one thing at a time, blocking | cooperative -- yields at `await` points |
| Best for | CPU-bound work, simple scripts | I/O-bound work (network, disk, DB) |
| Cost per unit of concurrency | a full OS thread (if using threading) | a lightweight coroutine |
| Speeds up CPU-bound code? | n/a | **no** -- see §9 |
| AI use case | a single, one-off script | serving many concurrent requests, fanning out API calls |

## 8. 🎯 AI Engineering Use Case

Calling an LLM, a vector DB, and a search API one after another wastes time waiting on each
in turn. Awaiting them *concurrently* means Python starts all three waits together and only
pays for the slowest one.

### Example A — Tiny

```python
async def fetch(name: str) -> str:
    await asyncio.sleep(0.1)
    return name
```

### Example B — Practical

```python
async def load_config_and_warm_cache() -> None:
    config = await load_config()      # e.g. from a remote config service
    await warm_cache(config)
```

### Example C — AI Engineering

```python
CALLS = [("llm", 0.5), ("vector_db", 0.3), ("search_api", 0.4)]

async def fake_api_call(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} result"

# sequential: ~1.2s (sum of all three delays)
for name, delay in CALLS:
    await fake_api_call(name, delay)

# concurrent: ~0.5s (the single slowest delay)
await asyncio.gather(*(fake_api_call(name, delay) for name, delay in CALLS))
```

Full runnable version, with measured timings:
[`examples/fanout_io_bound.py`](examples/fanout_io_bound.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
asyncio
✅ Use for:
- I/O-bound operations: HTTP calls, DB queries, file/network reads
- serving many concurrent requests in a web backend (FastAPI, etc.)
- fanning out independent calls (LLM + vector DB + search) to run together

❌ Don't expect it to:
- speed up CPU-heavy Python code (tight loops, number crunching, image processing)
- parallelize work across multiple CPU cores by itself
- make blocking calls (`time.sleep`, blocking DB drivers) non-blocking just by
  putting them inside an `async def`

BETTER ALTERNATIVE
Use `multiprocessing` (see `25-gil-processes-threads`) for CPU-bound work that
needs true parallelism. Use threads for blocking I/O in libraries with no async
API. Runnable proof asyncio doesn't help CPU-bound work:
[`examples/cpu_bound_no_speedup.py`](examples/cpu_bound_no_speedup.py)
```

## 10. 🚨 Common Mistakes

**Mistake 1 — forgetting `await`**

```python
# WRONG -- `result` is a coroutine OBJECT, not the string it will eventually produce.
# The function body never runs; Python even warns "coroutine was never awaited".
result = fetch_llm_response("hello")
print(result)  # <coroutine object fetch_llm_response at 0x...>
```

```python
# BETTER
result = await fetch_llm_response("hello")
print(result)  # response to: hello
```

Runnable proof: [`examples/forgot_await.py`](examples/forgot_await.py)

**Mistake 2 — blocking the event loop with `time.sleep()` (or any blocking call)**

```python
# WRONG -- time.sleep() blocks the ENTIRE event loop, not just this coroutine.
# Two "concurrent" workers end up running one after another: ~2s total.
async def worker(name: str) -> None:
    time.sleep(1)
```

```python
# BETTER -- asyncio.sleep() yields control back to the loop.
# Two concurrent workers now genuinely overlap: ~1s total.
async def worker(name: str) -> None:
    await asyncio.sleep(1)
```

Runnable proof with measured timings:
[`examples/blocking_vs_nonblocking.py`](examples/blocking_vs_nonblocking.py)

**Mistake 3 — assuming `asyncio.gather` makes CPU-bound work faster**

```python
# WRONG ASSUMPTION -- gathering two CPU-heavy coroutines does NOT run them in
# parallel. Neither one ever awaits anything, so neither yields control; total
# time is the same as running them one after another.
await asyncio.gather(cpu_bound(n), cpu_bound(n))
```

Runnable proof: [`examples/cpu_bound_no_speedup.py`](examples/cpu_bound_no_speedup.py) --
use `multiprocessing` instead (module `25`).

## 11. ⚡ Quick Tricks

```python
result = await asyncio.gather(...)
```

```python
# Run a top-level coroutine as a script's entry point
asyncio.run(main())
```

```python
# Sleep without blocking the event loop
await asyncio.sleep(1)
```

```python
# Check if you're accidentally holding a coroutine object instead of a result
import inspect
assert not inspect.iscoroutine(result), "did you forget an await?"
```

## 12. Performance Considerations

- Coroutines are far cheaper than OS threads -- thousands of them can be scheduled with
  minimal memory overhead, since Python only needs to save/restore local state at `await`
  points, not a full thread's stack.
- asyncio is single-threaded: it removes *waiting* time, not *computing* time. A CPU-bound
  coroutine with no `await` inside will run to completion before the loop can do anything
  else -- see [`examples/cpu_bound_no_speedup.py`](examples/cpu_bound_no_speedup.py).

## 13. 🎤 Interview Questions

**Q: Why doesn't asyncio automatically make CPU-bound Python faster?**
A: asyncio achieves concurrency by yielding control at `await` points while something else
(I/O) is happening. A CPU-bound function has no I/O to wait on -- it never yields -- so it
occupies the single event-loop thread from start to finish, exactly like a normal blocking
function call. True CPU parallelism needs multiple OS processes (`multiprocessing`), which
sidestep the GIL.

**Q: What happens when you forget `await`?**
A: The coroutine function call returns a coroutine object instead of running the function
body. No error is raised at the call site, but you get a `RuntimeWarning: coroutine '...' was
never awaited`, and any code relying on the (missing) return value silently breaks.

**Q: What's the difference between a coroutine and a Task?**
A: A coroutine is a paused computation that does nothing until awaited or scheduled. A Task
(created via `asyncio.create_task` or implicitly by `asyncio.gather`) wraps a coroutine and
schedules it to run on the event loop independently -- it starts making progress even before
you `await` it, which is what enables true concurrency between multiple coroutines.

**Q: Why is calling `time.sleep()` inside an `async def` function considered a serious bug in
a server context?**
A: It blocks the entire event loop's single thread for that duration, so every other
in-flight coroutine (every other user's request, in a web server) is frozen too -- not just
the one function that called it.

## 14. 🛠 Mini Exercise

Write an async function `fetch_all(urls: list[str])` that "fetches" each URL by awaiting
`asyncio.sleep(0.2)` and returning `f"{url}: ok"`, run **concurrently** for all URLs. Then
write a small `main()` that times both a sequential (`for url in urls: await fetch(url)`) and
a concurrent (`asyncio.gather`) version and prints both durations.

<details>
<summary>Solution</summary>

```python
import asyncio
import time


async def fetch(url: str) -> str:
    await asyncio.sleep(0.2)
    return f"{url}: ok"


async def fetch_all(urls: list[str]) -> list[str]:
    return await asyncio.gather(*(fetch(url) for url in urls))


async def main() -> None:
    urls = [f"https://api.example.com/{i}" for i in range(5)]

    start = time.perf_counter()
    for url in urls:
        await fetch(url)
    print(f"sequential: {time.perf_counter() - start:.2f}s")  # ~1.0s

    start = time.perf_counter()
    await fetch_all(urls)
    print(f"concurrent: {time.perf_counter() - start:.2f}s")  # ~0.2s


asyncio.run(main())
```

</details>

## 15. Real-World Challenge

Extend [`examples/fanout_io_bound.py`](examples/fanout_io_bound.py) so that one of the three
fake calls (e.g. `search_api`) sometimes "fails" by raising an exception instead of returning,
and make `concurrent()` still return the two successful results instead of the whole gather
call blowing up. (Hint: look at `asyncio.gather`'s `return_exceptions` parameter -- proper
retry/error handling is covered in depth in `15-error-handling-retries`.)

## 16. Cheat Sheet

```text
ASYNCIO FUNDAMENTALS
↓

async def f(): ...       defines a coroutine FUNCTION
f()                       calling it -> a coroutine OBJECT (nothing runs yet)
await f()                 runs it, yields control while waiting, returns its result
asyncio.run(main())       entry point for a top-level async program
asyncio.sleep(n)          non-blocking wait -- yields control back to the loop
asyncio.gather(*coros)    run multiple coroutines concurrently, wait for all results

WHEN TO USE
-> I/O-bound work: HTTP calls, DB queries, concurrent API fan-out

COMMON MISTAKE
-> time.sleep() or any blocking call inside async code freezes the WHOLE event loop

AI USE CASE
-> await asyncio.gather(llm_call(), vector_db_call(), search_call())
   # pay for the slowest call, not the sum of all three
```

---

⬅ Back to [main README](../README.md)
