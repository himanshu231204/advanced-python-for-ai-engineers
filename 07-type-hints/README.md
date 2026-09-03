# 07 — Type Hints

**Level:** 2 (Production Python) | **Status:** ✅ Written

Typed interfaces make agent/tool contracts safe and self-documenting -- critical once
multiple tools, models, and services need to agree on data shapes. This module covers the
practical core: basic hints, `TypedDict`, `Literal`, `Callable`, `TypeVar`, a `Protocol`
preview, and `Annotated`. The deep dive into generics and `Protocol` lives in
`11-protocols-generics`; Pydantic's *runtime* validation (which type hints alone don't give
you) is `09-pydantic`.

---

## 1. What is it?

Type hints are optional annotations on variables, parameters, and return values that describe
what type of value is expected. Python itself **does not enforce them at runtime** -- they
exist for readability, IDE autocomplete, and a separate static type checker (mypy, pyright) to
catch mismatches before the code ever runs.

## 2. Why does it exist?

```text
Python Concept
      ↓
typing
      ↓
safe agent interfaces
```

As a codebase grows -- more tools, more functions passed around, more dict-shaped payloads
flowing between an LLM and your business logic -- it gets easy to pass the wrong shape of data
without noticing until runtime. Type hints let a checker catch that mismatch statically,
before deployment, and let readers understand a function's contract without reading its body.

## 3. 💡 Mental Model

```text
def f(x: int) -> str: ...
         │        │
         │        └─ "this function returns a str" (a promise, not enforced by Python)
         └─ "this parameter should be an int" (also just a promise)
```

Think of type hints as a contract checked by a separate inspector (mypy/pyright), not by the
Python interpreter itself. Python will happily run code that violates its own type hints.

## 4. Syntax

```python
# Basic hints
name: str = "AI Engineer"
count: int = 3

def greet(name: str, times: int = 1) -> str:
    return (f"Hello, {name}! " * times).strip()

# Built-in generic containers (Python 3.9+ -- no `typing.List` needed)
names: list[str] = ["a", "b"]
scores: dict[str, int] = {"a": 1}

# Modern "optional" syntax (Python 3.10+)
def find(user_id: int) -> str | None: ...

# TypedDict -- shape for a plain dict
from typing import TypedDict
class Config(TypedDict):
    model: str
    temperature: float

# Literal -- restrict to specific values
from typing import Literal
Role = Literal["user", "assistant", "system"]

# Callable -- type a function value
from collections.abc import Callable
handler: Callable[[str], int] = len

# TypeVar -- link input/output types in a generic function
from typing import TypeVar
T = TypeVar("T")
def first(items: list[T]) -> T:
    return items[0]

# Annotated -- attach metadata to a type without changing the type itself
from typing import Annotated
TopK = Annotated[int, "must be between 1 and 20"]
```

## 5. Minimal Example

```python
def add(a: int, b: int) -> int:
    return a + b

add(2, 3)     # fine
add("2", "3")  # Python runs this too (string concatenation) -- a type
               # checker would flag it as wrong for THIS function's contract
```

## 6. What happens internally?

```text
def f(x: int) -> str: ...
        │
        ▼
Python stores the annotations in f.__annotations__ = {'x': int, 'return': str}
        │
        ▼
Nothing else happens at runtime -- no check, no conversion, no enforcement
        │
        ▼
A separate tool (mypy/pyright) reads __annotations__ / the source AST and
reports mismatches BEFORE the code runs -- Python itself never looks at this
```

## 7. Comparison: Type Hints vs Runtime Validation (Pydantic)

| | Type hints (`typing`) | Runtime validation (Pydantic, module 09) |
|---|---|---|
| Enforced when? | never, by Python itself | at object construction, every time |
| Checked by | a separate static tool (mypy/pyright) | the library itself, at runtime |
| Cost | zero runtime cost | some runtime cost (validation work) |
| Best for | internal function contracts, IDE support | validating untrusted external data (LLM output, API input) |
| AI use case | typing your own tool functions | validating structured LLM output before using it |

## 8. 🎯 AI Engineering Use Case

A typed tool-calling contract lets an agent, a tool registry, and a type checker all agree on
exactly what a tool call and its result look like -- before anything runs.

### Example A — Tiny

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

### Example B — Practical

```python
class Config(TypedDict):
    model: str
    temperature: float
```

### Example C — AI Engineering

```python
class ToolCall(TypedDict):
    name: str
    arguments: dict[str, object]

class ToolResult(TypedDict):
    status: Literal["ok", "error"]
    output: str

def dispatch(call: ToolCall) -> ToolResult:
    tool = TOOLS[call["name"]]
    return tool(**call["arguments"])
```

Full runnable version: [`examples/typed_tool_interface.py`](examples/typed_tool_interface.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
TYPE HINTS
✅ Good for:
- documenting and enforcing (statically) function/class contracts
- catching shape mismatches before deployment, via CI-run mypy/pyright
- typed tool/agent interfaces shared across a codebase

❌ Avoid when:
- treating them as runtime safety -- they do NOT validate untrusted input
  (LLM output, request bodies) at runtime
- over-annotating trivial, obvious local variables just for the sake of it

BETTER ALTERNATIVE
Use Pydantic (module 09) when you need ACTUAL runtime validation of data
you don't control the shape of (LLM structured output, API request bodies).
```

## 10. 🚨 Common Mistakes

**Mistake 1 — assuming type hints validate data at runtime**

```python
# WRONG ASSUMPTION -- Python runs this without complaint even though the
# type hint says `age: int`. Type hints are NOT a runtime guard.
def register(age: int) -> None:
    print(f"registered, age={age}")

register("not a number")  # runs fine, prints "registered, age=not a number"
```

```python
# BETTER -- validate at the boundary if the data is untrusted (see 09-pydantic)
from pydantic import BaseModel

class Registration(BaseModel):
    age: int

Registration(age="not a number")  # raises a real ValidationError
```

**Mistake 2 — using a bad Literal value and not catching it because mypy wasn't run**

```python
# WRONG -- this violates the ChatMessage TypedDict's Role Literal, but
# Python runs it anyway. Only a type checker catches it.
message: ChatMessage = {"role": "moderator", "content": "hi"}
```

Confirmed with `mypy`:

```text
error: Value of "role" has incompatible type "Literal['moderator']";
expected "Literal['system', 'user', 'assistant']"  [typeddict-item]
```

```python
# BETTER -- use one of the Literal's actual allowed values
message: ChatMessage = {"role": "user", "content": "hi"}
```

Runnable proof: [`examples/typed_dict_and_literal.py`](examples/typed_dict_and_literal.py)

**Mistake 3 — never actually running a type checker in CI**

```python
# WRONG -- type hints with no static checker ever run against them provide
# almost no benefit beyond documentation; mismatches silently accumulate.
```

```bash
# BETTER -- run mypy (or pyright) as part of CI, so hints are actually enforced
mypy src/
```

## 11. ⚡ Quick Tricks

```python
# Modern optional/union syntax -- no typing.Optional/Union import needed
def find(x: int) -> str | None: ...
value: int | str = 5
```

```python
# Built-in generics -- no typing.List/Dict/Tuple needed (Python 3.9+)
items: list[str] = []
mapping: dict[str, int] = {}
```

```python
# Type a callback parameter precisely
from collections.abc import Callable
def on_complete(callback: Callable[[str], None]) -> None: ...
```

```python
# Check what mypy/pyright would actually see, from Python itself
import typing
print(typing.get_type_hints(my_function))
```

## 12. Performance Considerations

- Type hints have zero runtime cost by themselves -- they're metadata, not executed code
  (with `from __future__ import annotations`, they're not even evaluated at all, just stored
  as strings).
- The real cost is in *validation* libraries (Pydantic) that use type hints to do actual
  runtime checking -- that's a deliberate, worthwhile tradeoff at trust boundaries, not
  something to add everywhere by default.

## 13. 🎤 Interview Questions

**Q: Do Python type hints get enforced at runtime?**
A: No. Python stores them (in `__annotations__`) but never checks them during normal
execution. Enforcement comes from a separate static analysis tool (mypy, pyright) run
separately, typically in CI or an editor -- or from a library like Pydantic that explicitly
performs runtime validation using type hints as its schema.

**Q: Why use Pydantic instead of plain dictionaries (or TypedDict) for LLM structured
output?**
A: A `TypedDict` only provides *static* shape-checking -- it does nothing at runtime, so
malformed LLM output (a missing field, wrong type) would silently corrupt your data or crash
somewhere downstream. Pydantic actively validates every field when the object is constructed,
raising a clear error immediately if the LLM's output doesn't match the expected shape.

**Q: What's the difference between `TypeVar` and `Generic`?**
A: `TypeVar` declares a placeholder type variable used to link related types across a
function's or class's signature (e.g. "the input list and the returned single item are the
same type `T`"). `Generic` is the base class a *class* inherits from to become
parameterizable by one or more `TypeVar`s (e.g. `class Box(Generic[T])`). Full depth on both
is in `11-protocols-generics`.

**Q: What does `Literal["a", "b"]` buy you over just typing something as `str`?**
A: It narrows the type to a specific, enumerable set of allowed values, so a type checker can
catch a typo or an invalid value (like `"moderator"` where only `"system"`, `"user"`, or
`"assistant"` are valid) at check time -- a plain `str` would accept literally anything.

## 14. 🛠 Mini Exercise

Define a `TypedDict` called `SearchResult` with `title: str`, `url: str`, and
`score: float`, and write a function `top_result(results: list[SearchResult]) -> SearchResult
| None` that returns the result with the highest `score`, or `None` if the list is empty.

<details>
<summary>Solution</summary>

```python
from typing import TypedDict


class SearchResult(TypedDict):
    title: str
    url: str
    score: float


def top_result(results: list[SearchResult]) -> SearchResult | None:
    if not results:
        return None
    return max(results, key=lambda r: r["score"])


results: list[SearchResult] = [
    {"title": "A", "url": "http://a", "score": 0.5},
    {"title": "B", "url": "http://b", "score": 0.9},
]
print(top_result(results))  # {'title': 'B', 'url': 'http://b', 'score': 0.9}
print(top_result([]))  # None
```

</details>

## 15. Real-World Challenge

Extend [`examples/typed_tool_interface.py`](examples/typed_tool_interface.py) so `ToolCall`
uses a `Literal` of the actual registered tool names (e.g. `Literal["search_docs"]`) instead
of a plain `str` for `name`, and confirm with `mypy` that calling `dispatch` with an unknown
tool name is now flagged statically, not just handled at runtime.

## 16. Cheat Sheet

```text
TYPE HINTS
↓

def f(x: int) -> str: ...        class C(TypedDict):        Role = Literal["a", "b"]
x: list[str] = []                    field: int
y: int | None = None

Callable[[str], int]             TypeVar("T")                Annotated[int, "metadata"]

WHEN TO USE
-> documenting/statically checking function contracts and typed interfaces

COMMON MISTAKE
-> assuming a type hint validates untrusted data at runtime (it does not)

AI USE CASE
-> TypedDict + Literal for a typed tool-call/result contract between agent and tools
```

---

⬅ Back to [main README](../README.md)
