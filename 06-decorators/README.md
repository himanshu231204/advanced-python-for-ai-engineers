# 06 — Decorators

**Level:** 1 (Modern Python Core) | **Status:** ✅ Written

Decorators are how retries, logging, tracing, and caching get layered onto LLM calls and tool
functions without cluttering business logic. This module leans directly on module `01`
(functions as first-class objects, `*args`/`**kwargs`) -- if that one made sense, decorators
are mostly a new way to combine ideas you already have.

---

## 1. What is it?

A decorator is a function that takes a function (or class) and returns a replacement for it
-- usually a wrapper that adds behavior before/after calling the original. `@decorator` above
a `def` is just syntax sugar: `func = decorator(func)`.

## 2. Why does it exist?

```text
LLM function
   ↓
retry
   ↓
logging
   ↓
tracing
   ↓
function
```

Cross-cutting concerns (retry logic, logging, timing, auth checks) apply to many unrelated
functions. Without decorators you'd copy-paste the same wrapping code into every function, or
tangle it directly into business logic. Decorators let you write that behavior once and apply
it declaratively.

## 3. 💡 Mental Model

```text
@decorator
def func(): ...

# is exactly the same as:

def func(): ...
func = decorator(func)
```

Whatever `func` refers to after that point is decorator's *return value*, not the original
function -- which is exactly why forgetting `functools.wraps` (§10) causes real problems.

## 4. Syntax

```python
from collections.abc import Callable
from typing import TypeVar
import functools

R = TypeVar("R")

def my_decorator(fn: Callable[..., R]) -> Callable[..., R]:
    @functools.wraps(fn)                      # preserves fn's __name__, __doc__, etc.
    def wrapper(*args: object, **kwargs: object) -> R:
        # ... code before ...
        result = fn(*args, **kwargs)
        # ... code after ...
        return result
    return wrapper

@my_decorator
def greet(name: str) -> str:
    return f"Hello, {name}!"

# Decorator WITH its own arguments needs an extra level of nesting:
def retry(times: int):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ...
        return wrapper
    return decorator

@retry(times=3)
def flaky(): ...
```

## 5. Minimal Example

```python
def log_call(fn):
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper

@log_call
def add(a, b):
    return a + b

add(2, 3)  # prints "calling add", then returns 5
```

## 6. Step-by-Step Execution

```text
@log_call
def add(a, b): ...
        │
        ▼
at IMPORT time: `add` is immediately replaced with `log_call(add)`'s
return value (the `wrapper` function) -- this happens once, not per call
        │
        ▼
add(2, 3)   # this actually calls `wrapper(2, 3)`
        │
        ▼
wrapper runs its own code, then calls the ORIGINAL `add` (captured in
its closure as `fn`), then runs any code after that call, then returns
```

## 7. Comparison: Function Decorator vs Class Decorator vs Parameterized Decorator

| | Plain function decorator | Class-based decorator (`__call__`) | Parameterized decorator (`@retry(times=3)`) |
|---|---|---|---|
| Nesting | one level (`decorator(fn)`) | a class instance replaces the function | two levels (`retry(times)` returns a decorator) |
| Holds state? | only via closures | yes, naturally (instance attributes) | yes, via closure over its own arguments |
| Best for | simple, stateless wrapping | wrapping that needs per-function state (call counts, caches) | wrapping that needs configuration (retry count, timeout) |
| AI use case | basic logging | per-tool call-count/cache | `@retry(times=3)`, `@timeout(seconds=5)` around LLM calls |

## 8. 🎯 AI Engineering Use Case

Retry, logging, and timing around an LLM call are the textbook case: each concern is a
separate, reusable decorator, stacked on the function that actually calls the model.

### Example A — Tiny

```python
def log_call(fn):
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper
```

### Example B — Practical

```python
def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        print(f"{fn.__name__} took {time.perf_counter() - start:.3f}s")
        return result
    return wrapper
```

### Example C — AI Engineering

```python
@timed
@logged
@retry(times=2)
def call_llm(prompt: str) -> str:
    ...
```

Full runnable version showing the exact execution order:
[`examples/stacked_decorators.py`](examples/stacked_decorators.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
DECORATORS
✅ Good for:
- cross-cutting concerns that apply to many functions (logging, retry, timing, auth)
- adding behavior without changing a function's internal logic or signature
- composable, stackable wrapping (retry + logging + tracing together)

❌ Avoid when:
- the "wrapping" logic is only needed in one specific place -- a plain helper
  function or inline code is clearer than a decorator used exactly once
- the decorator needs to change based on runtime values that aren't known
  until inside the wrapped function -- that's just normal control flow, not
  a decorator's job

BETTER ALTERNATIVE
For one-off wrapping, just write the code inline or as a normal helper
function -- decorators earn their complexity through reuse across many
functions.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — forgetting `functools.wraps`**

```python
# WRONG -- the decorated function loses its own __name__ and __doc__,
# which breaks introspection, debugging, and some frameworks' internals.
def log_call(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

@log_call
def greet(name: str) -> str:
    """Return a greeting."""
    ...

greet.__name__  # 'wrapper'  <- wrong!
```

```python
# BETTER
import functools

def log_call(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

greet.__name__  # 'greet'  <- correct
```

Runnable proof: [`examples/functools_wraps.py`](examples/functools_wraps.py)

**Mistake 2 — a parameterized decorator missing its extra nesting level**

```python
# WRONG -- `retry` needs to itself return a decorator, but this treats
# `times` as if it were the function being decorated.
def retry(times):
    def wrapper(*args, **kwargs):
        ...
    return wrapper

@retry(times=3)  # TypeError or silently broken -- `fn` is never captured correctly
def flaky(): ...
```

```python
# BETTER -- three levels: retry(times) -> decorator(fn) -> wrapper(*args, **kwargs)
def retry(times):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            ...
        return wrapper
    return decorator
```

Runnable version: [`examples/decorator_with_arguments.py`](examples/decorator_with_arguments.py)

**Mistake 3 — a decorator that swallows exceptions silently**

```python
# WRONG -- catches everything and never re-raises, hiding real bugs behind
# what looks like a successful call.
def safe(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None  # caller has no idea anything went wrong
    return wrapper
```

```python
# BETTER -- log/handle only what you actually intend to, then re-raise
# (or return a clearly-marked failure value) so failures stay visible.
def safe(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            logging.exception(f"{fn.__name__} failed")
            raise
    return wrapper
```

## 11. ⚡ Quick Tricks

```python
# Preserve the wrapped function's identity -- always do this
@functools.wraps(fn)
def wrapper(*args, **kwargs): ...
```

```python
# A decorator that works whether or not you pass it arguments needs
# no extra tricks if you always call it with parens: @retry() not @retry
```

```python
# Stack decorators bottom-up; the one closest to the function runs "first"
@timed
@retry(times=3)
def call_llm(): ...
```

```python
# Class-based decorator for stateful wrapping (call counts, per-function caches)
class CountCalls:
    def __init__(self, fn):
        functools.update_wrapper(self, fn)
        self.fn, self.calls = fn, 0
    def __call__(self, *a, **kw):
        self.calls += 1
        return self.fn(*a, **kw)
```

## 12. Performance Considerations

- Each layer of decoration adds one extra function call per invocation -- negligible for
  I/O-bound AI code (an LLM call dwarfs this), but worth remembering if decorating something
  in a tight, CPU-bound inner loop.
- A decorator's setup code (anything outside `wrapper`) runs once, at decoration time --
  expensive one-time setup belongs there, not inside `wrapper`, which runs on every call.

## 13. 🎤 Interview Questions

**Q: What does `@decorator` actually do under the hood?**
A: It's syntax sugar for `func = decorator(func)`, executed once when the module is loaded --
not once per call. Whatever `decorator` returns becomes the new value bound to `func`'s name.

**Q: Why is `functools.wraps` important?**
A: Without it, the decorated function's `__name__`, `__doc__`, and other metadata are replaced
by the wrapper function's own -- this breaks debugging output, documentation generation, and
any code that introspects the function (e.g. some routing/registration systems keyed on
function name).

**Q: How would you write a decorator that itself takes arguments, like `@retry(times=3)`?**
A: Add an extra level of nesting: an outer function (`retry`) that takes the configuration
arguments and returns the actual decorator function, which in turn takes `fn` and returns the
wrapper. `retry(times=3)` first runs and returns a decorator, which is then applied to the
function.

**Q: If you stack `@a` then `@b` above a function, which one runs first when the function is
called?**
A: `@b` (the one closest to the `def`) wraps the original function first, and `@a` wraps
*that* result. So execution order at call time is: `a`'s pre-call code, then `b`'s pre-call
code, then the original function, then `b`'s post-call code, then `a`'s post-call code.

## 14. 🛠 Mini Exercise

Write a decorator `once` that ensures the decorated function's body only ever actually runs
one time -- every subsequent call returns the cached result from the first call without
re-executing the function.

<details>
<summary>Solution</summary>

```python
import functools
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


def once(fn: Callable[[], R]) -> Callable[[], R]:
    sentinel = object()
    cached: object = sentinel

    @functools.wraps(fn)
    def wrapper() -> R:
        nonlocal cached
        if cached is sentinel:
            cached = fn()
        return cached  # type: ignore[return-value]

    return wrapper


calls = {"count": 0}


@once
def expensive_setup() -> str:
    calls["count"] += 1
    return "initialized"


print(expensive_setup())  # initialized
print(expensive_setup())  # initialized (fn body did NOT run again)
print(calls["count"])  # 1
```

</details>

## 15. Real-World Challenge

Extend [`examples/decorator_with_arguments.py`](examples/decorator_with_arguments.py)'s
`retry` decorator so it only retries specific exception types (e.g. `retry(times=3,
exceptions=(RuntimeError, TimeoutError))`) and re-raises immediately for anything else --
this is the actual shape `15-error-handling-retries` builds on for real API retry logic.

## 16. Cheat Sheet

```text
DECORATORS
↓

def decorator(fn):              def retry(times):        class CountCalls:
    @functools.wraps(fn)            def decorator(fn):        def __init__(self, fn):
    def wrapper(*a, **kw):              @functools.wraps(fn)      functools.update_wrapper(self, fn)
        ...                             def wrapper(*a, **kw):     self.fn = fn
        return fn(*a, **kw)                 ...                def __call__(self, *a, **kw):
    return wrapper                      return wrapper             return self.fn(*a, **kw)
                                     return decorator

WHEN TO USE
-> cross-cutting concerns applied across many functions (retry, logging, timing)

COMMON MISTAKE
-> forgetting functools.wraps -- loses __name__/__doc__ on the decorated function

AI USE CASE
-> @timed @logged @retry(times=2) around an LLM call function
```

---

⬅ Back to [main README](../README.md)
