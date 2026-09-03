# 26 — Contextvars

**Level:** 4 (Deep Python) | **Status:** ✅ Written

`contextvars` is how request-scoped state (request IDs, user context) stays correctly
isolated across concurrent async tasks. Module 20 already used `ContextVar` for correlated
logging; this module explains the actual mechanism -- and why the older `threading.local`
tool genuinely breaks under asyncio.

---

## 1. What is it?

`contextvars.ContextVar` is a variable that can hold a *different* value in different
execution contexts, roughly one per async task, instead of one single shared value like a
regular global variable. Setting it in one task never affects another concurrently-running
task's view of it.

## 2. Why does it exist?

Request-scoped data (a request ID, the current user) needs to be readable from deeply nested
functions without threading it through every single function signature as a parameter. A
plain global variable can't do this safely once multiple requests run concurrently on the
same thread (exactly what asyncio does) -- `contextvars` was built specifically to make this
safe.

## 3. 💡 Mental Model

```text
regular global      -> ONE value, shared by everything, everywhere
threading.local      -> one value PER THREAD -- but asyncio tasks share ONE thread!
contextvars.ContextVar -> one value PER (async) execution context -- correctly isolated
                          even when everything runs on a single thread
```

## 4. Syntax

```python
import contextvars

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

token = request_id_var.set("req-123")   # set a value in the CURRENT context
request_id_var.get()                     # "req-123" -- read it from anywhere downstream
request_id_var.reset(token)              # restore whatever it was before .set()
```

## 5. Minimal Example

```python
import contextvars

user_var = contextvars.ContextVar("user", default="anonymous")

def whoami() -> str:
    return user_var.get()

user_var.set("alice")
print(whoami())  # alice
```

## 6. What happens internally?

```text
asyncio.gather(handle_request("A"), handle_request("B"))
        │
        ▼
each coroutine is wrapped in a Task; when a Task is CREATED, it copies
the current Context (a snapshot of every ContextVar's current value)
        │
        ▼
handle_request("A")'s task calls request_id_var.set("A") -- this mutates
ONLY that task's own copy of the context, not the original, not task B's
        │
        ▼
handle_request("B")'s task independently sets "B" in ITS OWN copy
        │
        ▼
each task's request_id_var.get() reads from its own isolated context --
correctly returning "A" and "B" respectively, never mixed up
```

## 7. Comparison: `threading.local` vs `contextvars.ContextVar`

| | `threading.local` | `contextvars.ContextVar` |
|---|---|---|
| Isolation unit | per OS thread | per (async) execution context |
| Works correctly under asyncio? | **no** -- all tasks share one thread's storage | yes -- isolated per task |
| Works correctly with real threads? | yes | yes |
| AI use case | legacy sync multi-threaded code | request-scoped state in any async web backend |

## 8. 🎯 AI Engineering Use Case

Attributing every tool call inside an agent's run to the correct user -- across many
concurrent requests -- without passing `user_id` through every single function.

### Example A — Tiny

```python
user_var = contextvars.ContextVar("user", default="anonymous")
user_var.set("alice")
```

### Example B — Practical

```python
async def handle_request(request_id: str) -> None:
    request_id_var.set(request_id)
    await do_work()  # anything called from here can read request_id_var.get()
```

### Example C — AI Engineering

```python
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="anonymous")

def log_tool_call(tool: str) -> ToolCallLog:
    return ToolCallLog(tool=tool, user_id=user_id_var.get())  # never passed explicitly

async def handle_agent_request(user_id: str, tool: str) -> ToolCallLog:
    user_id_var.set(user_id)
    return await run_tool(tool)
```

Full runnable version: [`examples/request_scoped_state.py`](examples/request_scoped_state.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
CONTEXTVARS
✅ Good for:
- request-scoped state in async web backends (request ID, current user)
- correlated logging (module 20) without passing IDs through every function
- anything that needs per-task isolation while running on a shared event loop

❌ Avoid when:
- the value genuinely belongs as an explicit function parameter -- don't
  reach for a ContextVar just to avoid passing an argument a couple of
  calls deep
- true global, shared-across-everything state is actually what's needed
  (rare, but a plain module-level variable is simpler when it applies)

BETTER ALTERNATIVE
Pass values as explicit parameters when the call chain is shallow --
reserve contextvars for state that genuinely needs to reach arbitrarily
deep, unpredictable call chains (logging, tracing, request context).
```

## 10. 🚨 Common Mistakes

**Mistake 1 — using `threading.local` for request-scoped state in async code**

```python
# WRONG -- asyncio runs every task on ONE thread, so threading.local's
# storage is SHARED across all concurrently-running tasks.
_thread_local = threading.local()
_thread_local.request_id = request_id  # every concurrent task shares this!
```

```python
# BETTER
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")
request_id_var.set(request_id)  # correctly isolated per task
```

Runnable proof of `threading.local` actually breaking under `asyncio.gather`:
[`examples/contextvars_vs_threadlocal.py`](examples/contextvars_vs_threadlocal.py)

**Mistake 2 — expecting a ContextVar set inside a task to leak out to the caller**

```python
# WRONG ASSUMPTION -- setting a ContextVar inside a gathered task does
# NOT propagate back to whatever created the task.
await asyncio.gather(handle_request("A"))
print(request_id_var.get())  # still the value from BEFORE gather, not "A"
```

```python
# CORRECT -- each task has its OWN copy; if you need a value out, return it
async def handle_request(request_id):
    request_id_var.set(request_id)
    ...
    return request_id_var.get()  # explicitly return what you need
```

Runnable proof: [`examples/task_isolation.py`](examples/task_isolation.py)

**Mistake 3 — reaching for a ContextVar where a normal parameter would do**

```python
# WRONG -- adds indirection with no real benefit for a one-level-deep call
def process(item):
    current_item_var.set(item)
    _process_impl()

def _process_impl():
    item = current_item_var.get()
```

```python
# BETTER -- just pass it
def process(item):
    _process_impl(item)

def _process_impl(item):
    ...
```

## 11. ⚡ Quick Tricks

```python
# Declare with a sensible default so .get() never raises
var: contextvars.ContextVar[str] = contextvars.ContextVar("name", default="-")
```

```python
# Save/restore around a scoped change
token = var.set(new_value)
try:
    ...
finally:
    var.reset(token)
```

```python
# Attach request context to every log line (module 20's pattern)
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True
```

## 12. Performance Considerations

- Reading/writing a `ContextVar` is very cheap -- effectively a dict lookup in the current
  context -- and adds no meaningful overhead compared to the async work it's typically used
  alongside.
- Context copying happens once per `Task` creation, not per `await` -- there's no repeated
  copying cost as a coroutine runs.

## 13. 🎤 Interview Questions

**Q: Why can't you use a plain global variable for request-scoped state in an async web
backend?**
A: A plain global is shared by every concurrently-running task on the event loop. If two
requests are being handled "at the same time" (interleaved on one thread, as asyncio does),
one request's write to the global would be visible to (and could corrupt) another's read.

**Q: Why does `threading.local` fail to solve this problem under asyncio, even though it
solves the analogous problem for real multi-threaded code?**
A: `threading.local` isolates storage per OS *thread*. asyncio runs all of its tasks on a
single thread, so every task shares the exact same `threading.local` storage -- there's no
per-task isolation, only per-thread, which doesn't help when everything is on one thread.

**Q: What does a `Task` actually copy when contextvars are involved?**
A: When an `asyncio.Task` is created, it copies the *current context* -- a snapshot of every
`ContextVar`'s current value at that moment. Changes made to a `ContextVar` inside that task
only affect its own copy, and are invisible to sibling tasks or to whatever created the task.

**Q: When would you choose an explicit function parameter over a `ContextVar`?**
A: When the value is only needed a call or two deep, or when explicitness genuinely aids
readability -- forcing every reader to know "this value comes from ambient context" has a
real cost. `ContextVar` earns its keep specifically when a value needs to reach arbitrarily
deep, unpredictable call chains (logging, tracing) without threading it through every
signature along the way.

## 14. 🛠 Mini Exercise

Write a context manager `with_user(user_id: str)` (using `contextvars` and
`contextlib.contextmanager`) that sets a `user_id_var` ContextVar for the duration of the
`with` block and automatically resets it to its previous value on exit, even if the block
raises.

<details>
<summary>Solution</summary>

```python
import contextvars
from contextlib import contextmanager
from collections.abc import Iterator

user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="anonymous")


@contextmanager
def with_user(user_id: str) -> Iterator[None]:
    token = user_id_var.set(user_id)
    try:
        yield
    finally:
        user_id_var.reset(token)


print(user_id_var.get())  # anonymous
with with_user("alice"):
    print(user_id_var.get())  # alice
print(user_id_var.get())  # anonymous -- restored, even without an exception
```

</details>

## 15. Real-World Challenge

Extend [`examples/request_scoped_state.py`](examples/request_scoped_state.py) with a second
`ContextVar` for a `trace_id`, and modify `log_tool_call` to include both `user_id` and
`trace_id` in its output -- practice managing multiple independent pieces of ambient
request-scoped context at once, as a real production tracing setup would.

## 16. Cheat Sheet

```text
CONTEXTVARS
↓

var = contextvars.ContextVar("name", default=...)   declare
token = var.set(value)                                set (returns a Token)
var.get()                                              read from anywhere downstream
var.reset(token)                                       restore the previous value

asyncio.Task creation -> copies the current Context    each task is isolated

WHEN TO USE
-> request-scoped state (request ID, current user) readable from deep, unpredictable call chains

COMMON MISTAKE
-> threading.local for async request context -- ALL tasks share one thread's storage

AI USE CASE
-> attribute every tool call/log line to the correct user across concurrent agent requests
```

---

⬅ Back to [main README](../README.md)
