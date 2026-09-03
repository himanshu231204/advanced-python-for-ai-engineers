# 01 — Functions

**Level:** 1 (Modern Python Core) | **Status:** ✅ Written

Functions are the base unit of every AI pipeline step, tool call, and API handler. Before
touching asyncio or decorators, you need a solid model of how Python actually binds and
passes arguments -- because every retry wrapper, tool dispatcher, and agent interface in this
repo is built on top of it.

---

## 1. What is it?

A function is a named, reusable block of code that takes input (parameters), does something,
and optionally returns output. Python functions are also **objects** -- they can be stored in
variables, passed as arguments, returned from other functions, and stored in data structures.

## 2. Why does it exist?

Without functions you'd repeat logic everywhere and have no way to parameterize behavior. In
AI systems specifically, functions are the unit that gets:

- wrapped by decorators (retry, logging, tracing -- see `06-decorators`)
- registered as a **tool** an LLM can call
- passed around as **strategies** (a scoring function, a retrieval function, a formatter)

## 3. 💡 Mental Model

```text
def name(positional, *args, keyword=default, **kwargs):
              │        │              │           │
              │        │              │           └─ extra keyword args -> dict
              │        │              └─ named arg with a fallback value
              │        └─ extra positional args -> tuple
              └─ must be supplied, in order, unless given a default
```

Think of a function call as **binding a dictionary of arguments to parameter names** --
`*args` and `**kwargs` exist purely to make that binding flexible.

## 4. Syntax

```python
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"

# positional call
greet("Alice")

# keyword call
greet(name="Bob", greeting="Hi")

# variable arguments
def call_tool(name: str, *args: object, **kwargs: object) -> None: ...

# keyword-only arguments (everything after the bare *)
def search(query: str, *, top_k: int = 5) -> None: ...

# positional-only arguments (everything before the bare /)
def divide(a: float, b: float, /) -> float:
    return a / b
```

## 5. Minimal Example

```python
def add(a: int, b: int) -> int:
    return a + b

print(add(2, 3))  # 5
```

## 6. Step-by-Step Execution

```text
call_tool("search", "rag pipelines", top_k=3)
        │
        ▼
Python matches arguments to parameters left to right:
  name  = "search"            (positional -> named parameter)
  args  = ("rag pipelines",)  (leftover positionals -> *args tuple)
  kwargs = {"top_k": 3}       (leftover keywords -> **kwargs dict)
        │
        ▼
function body executes with those local bindings
```

Defaults are evaluated **once**, when the `def` statement runs (import/module-load time) --
not on every call. That single fact explains the #1 mistake in this module (§10).

## 7. Comparison: Positional vs Keyword vs `*args`/`**kwargs`

| | Positional | Keyword | `*args` | `**kwargs` |
|---|---|---|---|---|
| Purpose | required, order matters | required or optional, order-free | unknown number of extra positional values | unknown number of extra named values |
| Syntax | `def f(a, b)` | `def f(a, b=1)` | `def f(*args)` | `def f(**kwargs)` |
| Caller sees | `f(1, 2)` | `f(a=1, b=2)` | `f(1, 2, 3, ...)` | `f(x=1, y=2, ...)` |
| Typical AI use case | simple, fixed-shape calls | config with sane defaults | forwarding args to a wrapped function | forwarding a tool-call's `arguments` dict |

## 8. 🎯 AI Engineering Use Case

Every LLM tool-calling framework reduces to this shape:

```text
LLM decides: {"name": "search_docs", "arguments": {"query": "...", "top_k": 3}}
        ↓
dispatch_tool_call(name, **arguments)
        ↓
matching Python function executes with those exact kwargs
```

See [`examples/tool_dispatcher.py`](examples/tool_dispatcher.py) for the full runnable
version -- a `TOOLS` registry plus a dispatcher that unpacks the LLM's `arguments` dict
straight into a function call with `**kwargs`.

### Example A — Tiny

```python
def add(a: int, b: int) -> int:
    return a + b
```

### Example B — Practical

```python
def format_currency(amount: float, *, currency: str = "USD", decimals: int = 2) -> str:
    return f"{amount:.{decimals}f} {currency}"
```

### Example C — AI Engineering

```python
def dispatch_tool_call(name: str, **kwargs: object) -> str:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOLS[name](**kwargs)
```

Full file: [`examples/tool_dispatcher.py`](examples/tool_dispatcher.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
*args / **kwargs
✅ Good for:
- forwarding arguments to a wrapped function (decorators, dispatchers)
- building tool-call routers where the argument shape varies per tool
- APIs that need to stay flexible as parameters are added later

❌ Avoid when:
- the function has a small, fixed, well-known set of parameters
  (explicit parameters are more readable and give you real autocomplete/type-checking)
- you're using **kwargs just to avoid deciding a function's real signature

BETTER ALTERNATIVE
Use explicit typed parameters (or a `TypedDict`/Pydantic model, see 07 & 09) when the
shape of the arguments is actually known and stable.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — mutable default arguments**

```python
# WRONG -- the list is created once, at def time, and shared across every call
def add_message(message: str, history: list[str] = []) -> list[str]:
    history.append(message)
    return history
```

```python
# BETTER -- use None as a sentinel, build a fresh list per call
def add_message(message: str, history: list[str] | None = None) -> list[str]:
    if history is None:
        history = []
    history.append(message)
    return history
```

Why it matters here specifically: this exact bug shows up as "conversation history from one
user leaking into another user's chat session" when the default is used as a shared buffer.
Runnable proof: [`examples/mutable_default_argument.py`](examples/mutable_default_argument.py)

**Mistake 2 — forgetting that `**kwargs` swallows typos silently**

```python
# WRONG -- a typo'd keyword doesn't raise, it just vanishes into **kwargs
def search_docs(query: str, **kwargs: object) -> str:
    top_k = kwargs.get("top_k", 3)
    ...

search_docs("asyncio", tok_k=5)  # typo: silently ignored, top_k stays 3
```

```python
# BETTER -- make the parameter explicit so a typo raises TypeError immediately
def search_docs(query: str, *, top_k: int = 3) -> str:
    ...
```

**Mistake 3 — closures capturing a loop variable by reference, not by value**

```python
# WRONG -- all three closures share the same `i`, which ends up 2
callbacks = [lambda: i for i in range(3)]
print([cb() for cb in callbacks])  # [2, 2, 2]
```

```python
# BETTER -- bind the current value as a default argument
callbacks = [lambda i=i: i for i in range(3)]
print([cb() for cb in callbacks])  # [0, 1, 2]
```

## 11. ⚡ Quick Tricks

```python
# Unpack a dict straight into keyword arguments
params = {"top_k": 3, "rerank": True}
search_docs("query", **params)
```

```python
# Forward *everything* a wrapper received to the wrapped function
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)
```

```python
# Force callers to use keywords for clarity on multi-arg functions
def create_agent(*, name: str, model: str, temperature: float = 0.0) -> None: ...
```

```python
# Force positional-only for performance-critical / order-obvious functions
def dot(a: float, b: float, /) -> float:
    return a * b
```

## 12. Performance Considerations

- `*args`/`**kwargs` add a small overhead (tuple/dict construction on every call) --
  irrelevant for I/O-bound AI code, but avoid them in hot inner loops of CPU-bound code.
- Default argument evaluation happens once at import time, so an expensive default (e.g.
  `default=load_config()`) runs once per process, not per call -- usually what you want, but
  surprising if you expected fresh state.

## 13. 🎤 Interview Questions

**Q: Why is `def f(items=[]):` considered dangerous?**
A: The default list is created once when the function is defined, not each call. Every
invocation that doesn't pass its own `items` shares and mutates that same list, so state
leaks across unrelated calls. Fix: default to `None` and create the list inside the function.

**Q: What's the difference between `*args` and `**kwargs`?**
A: `*args` collects extra **positional** arguments into a tuple; `**kwargs` collects extra
**keyword** arguments into a dict. Both let a function accept an open-ended set of inputs,
which is exactly what a generic tool dispatcher or decorator wrapper needs.

**Q: What does a keyword-only parameter (`def f(a, *, b):`) buy you?**
A: It forces callers to pass `b` by name, which makes call sites self-documenting and
prevents accidental positional misordering -- important once a function has more than 2-3
parameters, like `create_agent(*, name, model, temperature)`.

**Q: What is a closure, and where would you actually use one in an AI system?**
A: A closure is a function that captures variables from its enclosing scope, even after
that scope has returned. Used for rate limiters, memoized caches, and configuration-baked
callbacks (e.g. `make_retry(max_attempts=3)` returning a ready-to-use retry function).

## 14. 🛠 Mini Exercise

Write `make_counter(start: int = 0)` that returns a closure `increment()` which increases
and returns an internal counter each time it's called, independent of any other counter
created from the same factory. Then write `throttle(fn, *, max_calls)` that wraps a function
so it raises `RuntimeError` after `max_calls` invocations.

<details>
<summary>Solution</summary>

```python
from collections.abc import Callable
from typing import TypeVar

R = TypeVar("R")


def make_counter(start: int = 0) -> Callable[[], int]:
    count = start

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment


def throttle(fn: Callable[..., R], *, max_calls: int) -> Callable[..., R]:
    calls = 0

    def wrapper(*args: object, **kwargs: object) -> R:
        nonlocal calls
        if calls >= max_calls:
            raise RuntimeError("call limit exceeded")
        calls += 1
        return fn(*args, **kwargs)

    return wrapper
```

</details>

## 15. Real-World Challenge

Extend [`examples/tool_dispatcher.py`](examples/tool_dispatcher.py) so `dispatch_tool_call`
also accepts an optional `default: str = "unknown tool"` keyword-only argument, returning it
instead of raising when the tool name isn't registered -- without changing any existing
`@register_tool` function signatures.

## 16. Cheat Sheet

```text
FUNCTIONS
↓
def f(a, b=1, *args, c, d=2, **kwargs): ...
     │  │      │       │  │      │
     │  │      │       │  │      └─ extra kwargs -> dict
     │  │      │       │  └─ keyword-only, has default
     │  │      │       └─ keyword-only, required
     │  │      └─ extra positionals -> tuple
     │  └─ positional-or-keyword, has default
     └─ positional-or-keyword, required

WHEN TO USE *args/**kwargs
-> forwarding to a wrapped function, generic tool dispatch

COMMON MISTAKE
-> mutable default argument (list/dict) shared across calls

AI USE CASE
-> dispatch_tool_call(name, **arguments)  # LLM tool-calling
```

---

⬅ Back to [main README](../README.md)
