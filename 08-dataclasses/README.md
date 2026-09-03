# 08 — Dataclasses

**Level:** 2 (Production Python) | **Status:** ✅ Written

Dataclasses are a lightweight way to model internal state -- agent state, request/response
objects -- without the overhead of a full validation layer. Reach for Pydantic (`09-pydantic`)
instead when the data comes from outside your program (an LLM, an API) and needs to be
validated, not just stored.

---

## 1. What is it?

`@dataclass` is a class decorator that generates `__init__`, `__repr__`, and `__eq__`
automatically from a class's type-annotated attributes, eliminating the boilerplate of writing
those methods by hand.

## 2. Why does it exist?

```text
Python Concept
      ↓
dataclass
      ↓
internal state
```

Plenty of classes exist purely to hold a fixed set of related fields together (a point, a
config, a step in an agent's run). Writing `__init__`/`__repr__`/`__eq__` by hand for every
one of these is repetitive and easy to get subtly wrong (forgetting a field in `__eq__`, for
example). `@dataclass` generates all of it correctly from the field list alone.

## 3. 💡 Mental Model

```text
@dataclass
class Point:
    x: float
    y: float

# is roughly equivalent to writing __init__, __repr__, and __eq__ by hand,
# using x and y as the fields for all three
```

## 4. Syntax

```python
from dataclasses import dataclass, field, FrozenInstanceError

@dataclass
class Config:
    model: str
    temperature: float = 0.0             # a plain default is fine for immutable values

@dataclass
class State:
    history: list[str] = field(default_factory=list)  # REQUIRED for mutable defaults

@dataclass(frozen=True, slots=True)
class Immutable:
    value: str
# frozen=True   -> instances can't be mutated after creation (raises FrozenInstanceError)
# slots=True    -> no per-instance __dict__, lower memory, faster attribute access
```

## 5. Minimal Example

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
print(p)          # Point(x=1.0, y=2.0)
print(p == Point(1.0, 2.0))  # True
```

## 6. What happens internally?

```text
@dataclass
class Point:
    x: float
    y: float
        │
        ▼
the decorator reads Point.__annotations__ ({'x': float, 'y': float})
        │
        ▼
it generates and attaches __init__(self, x, y), __repr__(self), and
__eq__(self, other) as real methods on the class -- there is no runtime
magic after this; Point behaves exactly like a hand-written class from
here on
```

## 7. Comparison: Dataclass vs Plain Class vs Pydantic

| | Plain class | `@dataclass` | Pydantic `BaseModel` (module 09) |
|---|---|---|---|
| Boilerplate | write `__init__`/`__repr__`/`__eq__` by hand | generated from annotations | generated from annotations |
| Runtime validation | none (unless you add it) | **none** | yes -- raises on bad data |
| Cost | none extra | near-zero | validation overhead per instance |
| Best for | full custom behavior control | internal, trusted state (agent state, config you built yourself) | data from an LLM, API request bodies, anything untrusted |
| AI use case | rare -- usually overkill | agent state, tool-call records | structured LLM output validation |

## 8. 🎯 AI Engineering Use Case

An agent's run state -- its goal, the steps it's taken, whether it's finished -- is exactly
the kind of internal, trusted state a dataclass is built for: you construct it, you control
its shape, and it never needs to validate untrusted input.

### Example A — Tiny

```python
@dataclass
class Point:
    x: float
    y: float
```

### Example B — Practical

```python
@dataclass
class ConversationState:
    user_id: str
    history: list[str] = field(default_factory=list)
```

### Example C — AI Engineering

```python
@dataclass(frozen=True, slots=True)
class Step:
    action: str
    result: str

@dataclass(slots=True)
class AgentState:
    goal: str
    steps: list[Step] = field(default_factory=list)
    finished: bool = False

    def record(self, action: str, result: str) -> None:
        self.steps.append(Step(action=action, result=result))
```

Full runnable version: [`examples/agent_state.py`](examples/agent_state.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
DATACLASSES
✅ Good for:
- internal state and value objects you fully control (agent state, config,
  intermediate pipeline results)
- cutting __init__/__repr__/__eq__ boilerplate for simple data-holding classes
- immutable records (frozen=True) that should never change after creation

❌ Avoid when:
- the data comes from outside your program (LLM output, API request bodies)
  and needs actual validation -- a dataclass does NOT validate anything
- the class needs significant custom behavior beyond holding/comparing fields

BETTER ALTERNATIVE
Use Pydantic (module 09) for anything that needs runtime validation of
untrusted data. Use a plain class when a dataclass's generated methods
don't fit what the class actually needs to do.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — a mutable default value instead of `field(default_factory=...)`**

```python
# WRONG -- dataclasses actually raise a ValueError at class-definition time
# for this exact mistake, specifically because it's such a common bug
# (see module 01's mutable default argument trap for the underlying cause).
@dataclass
class ConversationState:
    history: list[str] = []
    # ValueError: mutable default <class 'list'> for field history is not
    # allowed: use default_factory
```

```python
# BETTER
from dataclasses import field

@dataclass
class ConversationState:
    history: list[str] = field(default_factory=list)
```

Runnable proof of correct, isolated instances: [`examples/field_defaults.py`](examples/field_defaults.py)

**Mistake 2 — assuming `@dataclass` validates types at runtime**

```python
# WRONG ASSUMPTION -- the type hints are NOT enforced; this constructs fine.
@dataclass
class Point:
    x: float
    y: float

Point(x="not a number", y="also not a number")  # no error at construction
```

```python
# BETTER -- use Pydantic if you actually need the values checked
from pydantic import BaseModel

class Point(BaseModel):
    x: float
    y: float

Point(x="not a number", y=2)  # raises a real ValidationError
```

**Mistake 3 — forgetting `frozen=True` for records that should never change**

```python
# WRONG -- nothing stops a "historical" step record from being edited after
# the fact, silently corrupting an audit trail.
@dataclass
class Step:
    action: str
    result: str

step = Step("search", "found 3 results")
step.result = "rewritten after the fact"  # allowed, and probably a bug
```

```python
# BETTER
@dataclass(frozen=True)
class Step:
    action: str
    result: str
```

Runnable proof: [`examples/frozen_and_slots.py`](examples/frozen_and_slots.py)

## 11. ⚡ Quick Tricks

```python
@dataclass(slots=True)
class Item:
    ...
```

```python
# Mutable default? Always field(default_factory=...), never a bare literal
history: list[str] = field(default_factory=list)
```

```python
# Compare two dataclass instances field-by-field for free
a == b  # True if every field matches, no custom __eq__ needed
```

```python
# Convert a dataclass instance to a plain dict (handy for JSON serialization)
from dataclasses import asdict
asdict(my_instance)
```

## 12. Performance Considerations

- `slots=True` removes each instance's `__dict__`, which both saves memory and speeds up
  attribute access -- worth using for any dataclass you'll create many instances of (e.g. one
  per agent step, one per streamed chunk).
- Dataclasses add no meaningful runtime cost over a hand-written class -- the generated
  methods are ordinary Python functions, not extra machinery.

## 13. 🎤 Interview Questions

**Q: Does `@dataclass` validate the types declared in its annotations?**
A: No. Type hints on a dataclass are purely for static analysis (mypy/pyright) and for
generating `__init__`'s signature -- nothing checks at runtime that a `float` field actually
received a `float`. Use Pydantic when you need that guarantee.

**Q: Why can't you write `history: list[str] = []` directly in a dataclass?**
A: Because it's the exact mutable-default-argument bug from module 01 -- the empty list would
be created once, at class definition time, and shared across every instance that doesn't
override it. Dataclasses actively detect this for common mutable types and raise a
`ValueError` at class-definition time rather than let the bug happen silently; the fix is
`field(default_factory=list)`, which calls `list()` fresh for each new instance.

**Q: What does `frozen=True` actually guarantee?**
A: That any attempt to set an attribute on an instance after `__init__` raises
`FrozenInstanceError`. Combined with the default `eq=True`, frozen dataclasses also become
hashable, so they can be used as dict keys or set members -- something a normal mutable
dataclass cannot do safely.

**Q: When would you choose a dataclass over a Pydantic model?**
A: When the data is internal and fully trusted -- you construct every instance yourself and
control exactly what values go in, so there's no need to pay Pydantic's validation cost or
pull in the dependency. Once the data originates outside your code (an LLM's structured
output, a request body), Pydantic's validation becomes worth its cost.

## 14. 🛠 Mini Exercise

Define a frozen, slotted dataclass `ToolCall` with fields `name: str` and
`arguments: dict[str, object]`, and a (non-frozen) dataclass `ToolCallLog` with a
`calls: list[ToolCall]` field (using the correct default) and a method `add(name, arguments)`
that appends a new `ToolCall` to the log.

<details>
<summary>Solution</summary>

```python
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    arguments: dict[str, object]


@dataclass(slots=True)
class ToolCallLog:
    calls: list[ToolCall] = field(default_factory=list)

    def add(self, name: str, arguments: dict[str, object]) -> None:
        self.calls.append(ToolCall(name=name, arguments=arguments))


log = ToolCallLog()
log.add("search_docs", {"query": "dataclasses"})
print(log.calls)
# [ToolCall(name='search_docs', arguments={'query': 'dataclasses'})]
```

</details>

## 15. Real-World Challenge

Extend [`examples/agent_state.py`](examples/agent_state.py)'s `AgentState` with a method
`to_summary() -> str` that renders the goal and all recorded steps as a single multi-line
string, and add a `duration_seconds: float | None = None` field that `finish()` sets using
`time.perf_counter()` captured at construction time -- practice combining a dataclass with a
small amount of real behavior beyond pure data-holding.

## 16. Cheat Sheet

```text
DATACLASSES
↓

@dataclass                          @dataclass(frozen=True, slots=True)
class Point:                        class Immutable:
    x: float                            value: str
    y: float

field(default_factory=list)         # required for mutable defaults

WHEN TO USE
-> internal, trusted state you fully control (agent state, config, records)

COMMON MISTAKE
-> a bare mutable default (list/dict) instead of field(default_factory=...)

AI USE CASE
-> @dataclass(slots=True) class AgentState: goal: str; steps: list[Step] = field(default_factory=list)
```

---

⬅ Back to [main README](../README.md)
