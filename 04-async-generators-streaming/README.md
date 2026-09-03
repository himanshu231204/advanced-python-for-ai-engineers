# 04 — Async Generators & Streaming

**Level:** 1 (Modern Python Core) | **Status:** ✅ Written

This is the exact pattern behind LLM token streaming: an async generator yielding tokens or
events that FastAPI (`14-streaming-sse-websockets`) turns into a Server-Sent Events response.
It's the direct combination of module `02` (generators) and module `03` (asyncio) -- if those
two make sense, this module is mostly new syntax around a familiar idea.

---

## 1. What is it?

An **async generator** is a function defined with `async def` that also uses `yield`. Like a
regular generator, it produces values lazily, one at a time -- but it can also `await` between
yields, so producing the next value can involve real asynchronous work (a network read, a
timer) without blocking anything else. It's consumed with `async for` instead of `for`.

## 2. Why does it exist?

A regular generator can't `await` inside it -- `yield` and `await` are two different pause
mechanisms and a plain `def` function can't use `await` at all. But streaming real async data
(tokens arriving from an LLM API, events off a websocket) needs *both*: lazy, one-at-a-time
production (generators) **and** non-blocking waits between values (async). Async generators
are Python's answer to needing both at once.

## 3. 💡 Mental Model

```text
LLM
 ↓
tokens/events              (produced over time, not all at once)
 ↓
async generator            (yields each token as it arrives, awaiting in between)
 ↓
FastAPI endpoint            (async for chunk in generator: write chunk to response)
 ↓
SSE                          (Server-Sent Events -- see 14-streaming-sse-websockets)
 ↓
Frontend
```

## 4. Syntax

```python
from collections.abc import AsyncIterator

async def stream_values(n: int) -> AsyncIterator[int]:
    for i in range(n):
        await asyncio.sleep(0.1)   # any real async wait goes here
        yield i

async def main() -> None:
    async for value in stream_values(3):   # async for, not for
        print(value)
```

The async iterator protocol underneath `async for` is `__aiter__` (returns `self`) and
`async def __anext__` (raises `StopAsyncIteration` when done) -- the direct async counterpart
of module 02's `__iter__`/`__next__`.

## 5. Minimal Example

```python
import asyncio
from collections.abc import AsyncIterator

async def countdown(n: int) -> AsyncIterator[int]:
    while n > 0:
        await asyncio.sleep(0.05)
        yield n
        n -= 1

async def main() -> None:
    async for value in countdown(3):
        print(value)  # 3  2  1

asyncio.run(main())
```

## 6. Step-by-Step Execution

```text
gen = countdown(3)              # nothing runs yet -- an async generator object is created
async for value in gen:
        │
        ▼
    calls `await gen.__anext__()`
        │
        ▼
    resumes the function body, runs until `await asyncio.sleep(0.05)`
        │
        ▼
    yields control to the event loop while sleeping (OTHER tasks can run here)
        │
        ▼
    resumes right after the sleep, hits `yield n`, pauses, returns n
        │
        ▼
    loop body runs with `value = n`; then asks for the next value again
        │
        ▼
    ...repeats until the function returns -> StopAsyncIteration -> loop ends
```

## 7. Generator vs Coroutine vs Async Generator

| | Generator (`yield`) | Coroutine (`async def`) | Async Generator (`async def` + `yield`) |
|---|---|---|---|
| Produces | multiple values, lazily | one value (its return), once | multiple values, lazily |
| Can `await`? | no | yes | yes |
| Consumed with | `for` / `next()` | `await` | `async for` |
| Protocol | `__iter__`/`__next__` | awaitable | `__aiter__`/`__anext__` |
| AI use case | paginating a local list | one async LLM call | streaming LLM tokens/events |

## 8. 🎯 AI Engineering Use Case

An async generator is what an LLM streaming endpoint yields from under the hood: each `yield`
is one token (or one SSE event) becoming available to send to the client immediately, instead
of buffering the whole response.

### Example A — Tiny

```python
async def countdown(n: int):
    while n > 0:
        await asyncio.sleep(0.05)
        yield n
        n -= 1
```

### Example B — Practical

```python
async def paginated_api_results(client, query: str):
    page = 1
    while True:
        results = await client.get(f"/search?q={query}&page={page}")
        if not results:
            return
        for item in results:
            yield item
        page += 1
```

### Example C — AI Engineering

```python
async def stream_llm_tokens(text: str) -> AsyncIterator[str]:
    for word in text.split(" "):
        await asyncio.sleep(0.05)  # stand-in for the network wait between tokens
        yield word + " "

async for token in stream_llm_tokens(prompt_response):
    send_to_client(token)  # e.g. an SSE `data: ...` write in a FastAPI endpoint
```

Full runnable version: [`examples/llm_token_stream.py`](examples/llm_token_stream.py). See
`14-streaming-sse-websockets` for wiring this into an actual FastAPI endpoint.

## 9. LangGraph/Agent Relevance

Agent frameworks stream intermediate steps (a tool call starting, a partial thought, a final
answer) the same way: each node in the graph can be an async generator yielding state updates
as they happen, instead of the caller waiting for the entire run to finish before seeing
anything. `28-ai-engineering-patterns` and Project 06 build on this directly.

## 10. WHEN TO USE / WHEN NOT TO

```text
ASYNC GENERATORS
✅ Good for:
- streaming data that arrives over time from an async source (LLM tokens, websocket
  events, paginated async API results)
- producing values lazily while doing real async I/O between them

❌ Avoid when:
- there's no actual async work between values -- a plain generator (module 02) is
  simpler and has less overhead
- you need all values before doing anything with them anyway -- just `await` a
  coroutine that returns a list

BETTER ALTERNATIVE
Use a plain generator when nothing between yields needs to be awaited. Use a single
coroutine returning a list when you need the complete result before proceeding.
```

## 11. 🚨 Common Mistakes

**Mistake 1 — using a blocking call instead of an async one inside an async generator**

```python
# WRONG -- time.sleep() blocks the whole event loop, defeating the entire point
# of making this an async generator in the first place.
async def stream_tokens(n: int):
    for i in range(n):
        time.sleep(0.1)
        yield i
```

```python
# BETTER
async def stream_tokens(n: int):
    for i in range(n):
        await asyncio.sleep(0.1)
        yield i
```

Runnable proof of the difference (with an interleaved heartbeat task):
[`examples/sync_vs_async_generator.py`](examples/sync_vs_async_generator.py)

**Mistake 2 — using `for` instead of `async for`**

```python
# WRONG -- raises TypeError: 'async_generator' object is not iterable
for value in stream_tokens(3):
    ...
```

```python
# BETTER
async for value in stream_tokens(3):
    ...
```

**Mistake 3 — no backpressure between a fast producer and a slow consumer**

```python
# WRONG -- an unbounded queue lets the producer race arbitrarily far ahead,
# buffering unlimited memory if the consumer can't keep up.
queue: asyncio.Queue = asyncio.Queue()  # no maxsize
```

```python
# BETTER -- a bounded queue makes queue.put() await until there's room,
# naturally slowing the producer to the consumer's pace.
queue: asyncio.Queue = asyncio.Queue(maxsize=100)
```

Runnable proof: [`examples/backpressure.py`](examples/backpressure.py)

## 12. Performance Considerations

- Each `await` point inside an async generator is a chance for the event loop to run other
  tasks -- this is what lets a slow token stream coexist with other concurrent requests in a
  server, unlike a sync generator with blocking calls (§11, Mistake 1).
- Unbounded buffering between a producer and consumer (no queue limit, or materializing an
  entire async generator into a list before processing) throws away the memory benefit that
  made streaming worth doing in the first place.

## 13. 🎤 Interview Questions

**Q: How would you stream an LLM response using an async generator?**
A: Write an `async def` function that `yield`s each token (or chunk) as it's produced,
`await`-ing the underlying network read between yields instead of blocking. A consumer (e.g.
a FastAPI endpoint) then does `async for chunk in stream: write(chunk)`, sending each piece to
the client immediately rather than waiting for the full response.

**Q: Why can't a regular generator use `await`?**
A: `yield` and `await` are different suspension mechanisms tied to different underlying
protocols (`__next__` vs the awaitable protocol driven by the event loop). A plain `def`
function's frame has no way to hand control to the event loop; only inside `async def` does
Python make that machinery available, which is why async generators require `async def` +
`yield` together.

**Q: What's backpressure, and why does it matter for streaming pipelines?**
A: Backpressure is a mechanism that slows a fast producer down to match a slower consumer,
usually via a bounded buffer (like `asyncio.Queue(maxsize=...)`) that blocks the producer once
full. Without it, a fast producer and slow consumer combination leads to unbounded memory
growth as unconsumed items pile up.

**Q: What exception does `async for` rely on to know a stream has ended?**
A: `StopAsyncIteration`, raised (implicitly, when the function body returns) by the async
generator's `__anext__` -- the async counterpart of `StopIteration` in module 02.

## 14. 🛠 Mini Exercise

Write an async generator `stream_with_progress(items: list[str])` that yields each item after
an `asyncio.sleep(0.1)`, and also prints `"N/total"` progress to stdout each time it yields
(without that progress text becoming part of what's yielded).

<details>
<summary>Solution</summary>

```python
import asyncio
from collections.abc import AsyncIterator


async def stream_with_progress(items: list[str]) -> AsyncIterator[str]:
    total = len(items)
    for i, item in enumerate(items, start=1):
        await asyncio.sleep(0.1)
        print(f"{i}/{total}")
        yield item


async def main() -> None:
    async for item in stream_with_progress(["a", "b", "c"]):
        print("got:", item)


asyncio.run(main())
```

</details>

## 15. Real-World Challenge

Extend [`examples/backpressure.py`](examples/backpressure.py) so the producer is itself an
async generator (`async def numbers(count) -> AsyncIterator[int]`) instead of a plain function
that calls `queue.put` directly, with a separate small coroutine that drains the generator
into the queue. This is closer to how a real pipeline looks: an async generator as the source
of truth, and a queue as the buffering/backpressure layer between it and a consumer.

## 16. Cheat Sheet

```text
ASYNC GENERATORS & STREAMING
↓

async def gen():              class C:
    while cond:                    def __aiter__(self): return self
        await something()          async def __anext__(self): ...
        yield value

async for x in gen():         consume with async for, not for

WHEN TO USE
-> streaming data with real async work between values (LLM tokens, websocket events)

COMMON MISTAKE
-> a blocking call (time.sleep) inside an async generator freezes the whole event loop

AI USE CASE
-> async for token in stream_llm_tokens(response): send_to_client(token)
```

---

⬅ Back to [main README](../README.md)
