# 05 — Context Managers

**Level:** 1 (Modern Python Core) | **Status:** ✅ Written

Context managers model resource and session lifecycles -- HTTP clients, DB connections, and
LLM client sessions all rely on deterministic setup/teardown. Every `async with
httpx.AsyncClient() as client:` you'll write later in this repo rests on the protocol covered
here.

---

## 1. What is it?

A context manager is any object that defines `__enter__` and `__exit__` (or `__aenter__`/
`__aexit__` for the async version), used with the `with` (or `async with`) statement. It
guarantees a cleanup step runs when the block ends -- whether it ends normally or via an
exception.

## 2. Why does it exist?

Manually pairing "acquire" and "release" calls is error-prone: it's easy to forget the release
on an early `return`, or skip it entirely when an exception is raised mid-block. `with`
guarantees the cleanup step (`__exit__`) always runs once the block is entered, regardless of
how it exits.

## 3. 💡 Mental Model

```text
with resource() as r:
    ...              <- __exit__ WILL run after this, no matter what happens here
```

Think of `with` as a promise: "no matter how this block ends -- return, break, exception --
the teardown code is guaranteed to run." It's a structured `try`/`finally` you don't have to
write by hand.

## 4. Syntax

```python
# Class-based (implement the protocol directly)
class Resource:
    def __enter__(self):
        ...
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        ...
        return False  # False/None = don't suppress exceptions

with Resource() as r:
    ...

# Function-based (the easy way, via contextlib)
from contextlib import contextmanager

@contextmanager
def resource():
    ...              # __enter__ code
    try:
        yield value
    finally:
        ...          # __exit__ code -- runs even if the block raises

# Async versions
class AsyncResource:
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc_value, traceback): ...

async with AsyncResource() as r:
    ...
```

## 5. Minimal Example

```python
from contextlib import contextmanager

@contextmanager
def open_resource(name: str):
    print(f"opening {name}")
    try:
        yield f"handle-to-{name}"
    finally:
        print(f"closing {name}")

with open_resource("db") as handle:
    print("using", handle)
# opening db
# using handle-to-db
# closing db
```

## 6. Step-by-Step Execution

```text
with Resource() as r:
    body()
        │
        ▼
1. Resource().__enter__() runs -> its return value is bound to `r`
2. body() executes
3. Whether body() finishes normally OR raises an exception,
   Resource().__exit__(exc_type, exc_value, traceback) runs
4. If __exit__ returns a truthy value, any exception from body() is
   SUPPRESSED. If it returns False/None (the default), the exception
   propagates normally after __exit__ finishes.
```

## 7. Comparison: Class-based vs `@contextmanager`

| | Class (`__enter__`/`__exit__`) | `@contextmanager` generator |
|---|---|---|
| Boilerplate | a full class, two methods | one function, one `yield` |
| State | instance attributes | local variables (closure) |
| Best for | reusable, multi-method resources (a client with other methods too) | one-off, simple setup/teardown |
| Async version | `__aenter__`/`__aexit__` | `@asynccontextmanager` |

## 8. 🎯 AI Engineering Use Case

Every async HTTP client, LLM SDK client, or connection pool is used exactly this way so that
the connection is guaranteed to close even if a request inside the block fails.

### Example A — Tiny

```python
with open_resource("db") as handle:
    use(handle)
```

### Example B — Practical

```python
import sqlite3

with sqlite3.connect("app.db") as conn:
    conn.execute("INSERT INTO logs VALUES (?)", ("started",))
# connection is committed/closed automatically, even if execute() raised
```

### Example C — AI Engineering

```python
@asynccontextmanager
async def llm_client():
    print("opening connection pool")
    client = LLMClient()
    try:
        yield client
    finally:
        print("connection pool closed")  # runs even if a request raised

async with llm_client() as client:
    result = await client.complete("hello")
```

Full runnable version, including the failure path:
[`examples/llm_session_manager.py`](examples/llm_session_manager.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
CONTEXT MANAGERS
✅ Good for:
- anything with a clear open/close, acquire/release, or begin/commit lifecycle
  (files, DB connections, HTTP clients, locks, temporary state changes)
- guaranteeing cleanup runs even when the block raises

❌ Avoid when:
- there's no real "cleanup" step needed -- a context manager just for
  running two lines of code before/after adds ceremony with no benefit
- the resource genuinely needs to outlive the current function's scope
  (e.g. a connection pool created once at app startup and reused everywhere)

BETTER ALTERNATIVE
For app-lifetime resources, create them once (e.g. in a FastAPI lifespan
handler or a startup function) rather than opening/closing per request.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — forgetting that `__exit__` runs even when the block raises**

```python
# WRONG ASSUMPTION -- believing cleanup only happens on the "happy path"
with open_resource("db") as handle:
    might_raise()
# cleanup already ran even if might_raise() threw -- code after the `with`
# that assumes the resource is "still open" is wrong
```

```python
# BETTER -- do anything that needs the resource still open INSIDE the block
with open_resource("db") as handle:
    might_raise()
    use(handle)  # keep resource-dependent work inside the `with`
```

**Mistake 2 — accidentally swallowing exceptions in `__exit__`**

```python
# WRONG -- returning True unconditionally silently discards every exception
# raised inside the block, including ones you never intended to catch.
def __exit__(self, exc_type, exc_value, traceback):
    self.close()
    return True  # swallows EVERYTHING, even KeyboardInterrupt-style bugs
```

```python
# BETTER -- only suppress the specific exception type you actually intend to handle
def __exit__(self, exc_type, exc_value, traceback):
    self.close()
    return exc_type is ValueError  # only ValueError is suppressed
```

**Mistake 3 — using a sync context manager for something that does async I/O**

```python
# WRONG -- __enter__/__exit__ can't `await`, so a real async handshake/
# teardown either blocks the event loop or can't run at all here.
class AsyncClient:
    def __enter__(self):
        asyncio.run(self.connect())  # blocks, and breaks inside a running loop
        return self
```

```python
# BETTER -- use __aenter__/__aexit__ with `async with` for anything that
# needs to await during setup/teardown.
class AsyncClient:
    async def __aenter__(self):
        await self.connect()
        return self
```

Runnable proof: [`examples/async_context_manager.py`](examples/async_context_manager.py)

## 11. ⚡ Quick Tricks

```python
async with httpx.AsyncClient() as client:
    ...
```

```python
# Multiple managers in one line -- entered left to right, exited right to left
with open("in.txt") as fin, open("out.txt", "w") as fout:
    ...
```

```python
# Turn any generator with one yield into a context manager
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{label}: {time.perf_counter() - start:.2f}s")
```

```python
# Suppress a specific expected exception without try/except
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove("maybe_missing.txt")
```

## 12. Performance Considerations

- `@contextmanager` adds a small amount of overhead versus a hand-written class (generator
  machinery + `try`/`finally`), which is irrelevant next to the cost of whatever resource
  you're managing (a network connection, a file).
- Prefer creating expensive resources (connection pools, HTTP clients) once and reusing them
  across many `with`/`async with` uses of their *methods*, rather than opening a brand-new
  client inside a hot loop.

## 13. 🎤 Interview Questions

**Q: What guarantee does a context manager actually give you?**
A: That `__exit__` (or `__aexit__`) runs once the block is entered, regardless of whether the
block completes normally, returns early, or raises an exception -- equivalent to a `finally`
block, but reusable and attached to the resource itself instead of duplicated at every call
site.

**Q: What does it mean if `__exit__` returns `True`?**
A: Any exception raised inside the `with` block is suppressed -- it will not propagate past
the `with` statement. Returning `False` (or `None`, the default) lets the exception propagate
normally after `__exit__` finishes running.

**Q: Why do async context managers need separate `__aenter__`/`__aexit__` methods instead of
just `__enter__`/`__exit__`?**
A: `__enter__`/`__exit__` are plain synchronous methods -- they cannot contain `await`.
Anything that needs to perform async I/O during setup or teardown (an async connection
handshake, an async close call) needs the `async def __aenter__`/`__aexit__` methods that
`async with` specifically looks for.

**Q: When would you choose a class-based context manager over `@contextmanager`?**
A: When the object needs other methods beyond just enter/exit (e.g. a client with `.get()`,
`.post()`, etc. in addition to being used as a context manager), or when the setup/teardown
state is complex enough that instance attributes are clearer than closure variables in a
generator function.

## 14. 🛠 Mini Exercise

Write a context manager `timer(label: str)` (using `@contextmanager`) that prints how long the
`with` block took to run, in seconds, labeled with `label` -- and make sure it still prints the
timing even if the block raises an exception.

<details>
<summary>Solution</summary>

```python
import time
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def timer(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")


with timer("fast path"):
    sum(range(1_000_000))

try:
    with timer("failing path"):
        raise ValueError("boom")
except ValueError:
    pass  # timer still printed its line before this exception propagated
```

</details>

## 15. Real-World Challenge

Extend [`examples/llm_session_manager.py`](examples/llm_session_manager.py) so `llm_client()`
takes a `max_retries: int` parameter and, if `client.complete()` raises inside the block,
retries the *entire block's* request up to `max_retries` times before finally letting the
exception propagate (hint: this needs to live around the caller's usage, not just inside the
context manager -- a proper retry decorator is covered in `06-decorators` and
`15-error-handling-retries`).

## 16. Cheat Sheet

```text
CONTEXT MANAGERS
↓

class C:                       @contextmanager
    def __enter__(self): ...   def resource():
    def __exit__(self, *exc):      setup()
        ...                        try:
        return False                   yield value
                                    finally:
                                        teardown()

async with httpx.AsyncClient() as client:
    ...

WHEN TO USE
-> anything with an open/close, acquire/release lifecycle

COMMON MISTAKE
-> __exit__ returning True unconditionally silently swallows ALL exceptions

AI USE CASE
-> async with llm_client() as client: ...  # guarantees cleanup even on failure
```

---

⬅ Back to [main README](../README.md)
