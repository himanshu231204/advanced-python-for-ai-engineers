# Functions and Scope Refresher — MUST KNOW

**Status:** ✅ Written | Python 3.12+

Scope mistakes can leak chat history between requests or break a tool counter. This
lesson covers name ownership; continue with [module 01](../01-functions/README.md)
for function signatures, argument passing, lambdas, and higher-order functions.

## 1. What is it?

Scope determines which binding a name refers to. A binding connects a name to an
object. Assignment can replace that connection; mutation changes the object itself.

## 2. Why does it exist?

Functions need private working names while still reading configuration and retaining
selected state. Explicit state ownership makes AI request handling easier to reason about.

## 3. 💡 Mental Model

For ordinary name reads inside nested functions, lookup follows **LEGB**:

```text
Local function -> Enclosing function(s) -> Global module -> Builtins -> NameError
```

Parameters are local bindings. Builtins include `len` and `sum`; a closer binding
can shadow them. An assignment anywhere in a function normally makes that name
local throughout that function, even before the assignment executes. Python does
not fall back to a global when that local binding has no value yet.

```text
caller name ----+----> list object <---- parameter name
                |          |
                |          +-- append(): shared object changes
                +-- parameter = []: only parameter binding changes
```

Class bodies and attribute lookup have additional rules; LEGB here describes
ordinary function name lookup, not `object.attribute` lookup.

## 4. Syntax

```python
from collections.abc import Callable

limit: int = 3

def make_budget() -> Callable[[], int]:
    remaining: int = limit

    def consume() -> int:
        nonlocal remaining
        remaining -= 1
        return remaining

    return consume

budget: Callable[[], int] = make_budget()
assert budget() == 2
assert budget() == 1
```

`nonlocal` rebinds an existing enclosing function binding; `global` rebinds a
module binding. Neither declaration is necessary merely to read that binding.

## 5. Minimal Example

**Example A — Tiny: local, enclosing, global, and builtin reads**

```python
prefix: str = "tool"

def describe() -> str:
    suffix: str = "ready"

    def render() -> str:
        separator: str = ":"
        return separator.join((prefix, suffix, str(len(suffix))))

    return render()

assert describe() == "tool:ready:5"
```

`separator` is local to `render`; `suffix` is enclosing; `prefix` is global;
`len` and `str` come from builtins.

## 6. Step-by-Step Execution

**Example B — Practical: update an order without replacing the caller's list**

```python
def add_item(items: list[str]) -> list[str]:
    items.append("tea")
    items = ["replacement"]
    return items

order: list[str] = ["bread"]
replacement: list[str] = add_item(order)
assert order == ["bread", "tea"]
assert replacement == ["replacement"]
```

1. The parameter and `order` initially reference the same list.
2. `append` mutates that shared list.
3. Assignment binds the local `items` to a different list.
4. Returning exposes the new list; `order` still references the original.

## 7. Comparison

| Operation | What changes? | AI use case | Caution |
|---|---|---|---|
| `name = value` | Binding in the selected scope | Local request result | Does not copy a mutable object |
| `items.append(value)` | Referenced list | Append a chat turn | All aliases observe mutation |
| `nonlocal count` | Enclosing binding on assignment | Per-session closure counter | Shared closure calls share state |
| `global count` | Module binding on assignment | Rare process-local instrumentation | Not request-local or cross-process |
| Explicit parameter/return | State passed by caller | Request history ownership | Caller must choose sharing policy |

## 8. 🎯 AI Engineering Use Case

**Example C — AI Engineering: independent request histories**

```python
def record_turn(prompt: str, history: list[str] | None = None) -> list[str]:
    turns: list[str] = [] if history is None else list(history)
    turns.append(prompt)
    return turns

first: list[str] = record_turn("Explain RAG")
second: list[str] = record_turn("Explain tools")
followup: list[str] = record_turn("Give an example", first)
assert first == ["Explain RAG"]
assert second == ["Explain tools"]
assert followup == ["Explain RAG", "Give an example"]
assert first is not second
```

A fresh list prevents accidental request-to-request leakage. Copying supplied
history also preserves the caller's list. This shallow copy is sufficient for
strings; nested mutable messages require a deliberate ownership/copy policy.

## 9. When to Use / When NOT to Use

WHEN TO USE
✅ Good for:
- Local variables and explicit parameters for request state.
- A closure when one owner intentionally retains a small counter or configuration.

WHEN NOT TO USE
❌ Avoid when:
- A module global would hold user-specific history.
- Multiple tasks or threads mutate a closure without a coordination policy.

BETTER ALTERNATIVE
Use explicit state objects and parameters instead when ownership must be visible;
use durable storage when state must survive restarts or span worker processes.

## 10. 🚨 Common Mistakes

**Wrong: read a global before assigning the same name locally.**

```python
count: int = 10

def broken() -> int:
    count += 1
    return count

try:
    broken()
except UnboundLocalError as error:
    assert isinstance(error, UnboundLocalError)
else:
    raise AssertionError("Expected an unbound local read")
assert count == 10
```

**Better: return an updated value and let the caller own it.**

```python
def increment(count: int) -> int:
    return count + 1

count: int = 10
count = increment(count)
assert count == 11
```

`+=` reads before writing. The function's local binding is uninitialized.
`global count` would change module state but would introduce hidden sharing.

**Wrong: a mutable default is created once, when the function is defined.**

```python
def shared_history(prompt: str, history: list[str] = []) -> list[str]:
    history.append(prompt)
    return history

first: list[str] = shared_history("request A")
second: list[str] = shared_history("request B")
assert first is second
assert first == ["request A", "request B"]
```

**Better:** use the `None` default and fresh list from section 8. A default tuple
is also suitable when the function only needs immutable input. Merely avoiding a
mutable default does not prevent sharing a mutable global or caller-owned object.

## 11. ⚡ Quick Tricks

A factory gives each owner an independent retained binding:

```python
from collections.abc import Callable

def make_counter() -> Callable[[], int]:
    count: int = 0

    def next_count() -> int:
        nonlocal count
        count += 1
        return count

    return next_count

session_a: Callable[[], int] = make_counter()
session_b: Callable[[], int] = make_counter()
assert (session_a(), session_a(), session_b()) == (1, 2, 1)
```

Mutation of an enclosing list needs no `nonlocal`; rebinding the enclosing name
does. Avoid naming variables `list`, `str`, or `len` to keep builtins available.

## 12. Performance Considerations

Fresh empty lists have constant setup cost; copying history takes O(n) time and
space. Choose ownership before optimizing copies. Closures keep referenced state
alive while reachable; do not capture an entire retrieval corpus for a tiny counter.
Globals are process-local, so a global counter is not a reliable multi-worker total.
Neither `global` nor `nonlocal` supplies synchronization for concurrent updates.

## 13. 🎤 Interview Questions

- **Why can a function read a global but fail on `count += 1`?** Assignment marks
  `count` local unless declared otherwise; the augmented assignment reads it first.
- **Does passing a list copy it?** No. The parameter references the same object;
  mutation is visible through aliases, while local rebinding is not.
- **Does each call recreate a mutable default?** No. Defaults are evaluated at
  definition time; use a sentinel such as `None` and allocate inside the call.
- **What does `nonlocal` target?** An existing binding in an enclosing function,
  not the module global. Different factory calls create independent bindings.

## 14. 🛠 Mini Exercise

Build a `make_token_total()` closure accepting an integer token count and returning
the accumulated total. Check calls with 3 then 2 return 3 then 5, and a second
factory starts at zero. Explain why it needs `nonlocal` for an integer binding.
Then explain why sharing one returned closure across requests shares its total.

## 15. Real-World / Runnable Code Example

Run [scope_and_references.py](examples/scope_and_references.py):

```bash
python 00-python-foundation-review/examples/scope_and_references.py
```

It checks independent request histories, mutation versus rebinding, independent
closure factories, retained closure state, and a caught `UnboundLocalError`.
For full function design, continue to [module 01](../01-functions/README.md).

## 16. Cheat Sheet

| Need | Rule |
|---|---|
| Resolve an ordinary function name | Local → Enclosing → Global → Builtins |
| Replace a local binding | `name = value` |
| Change a referenced list | `items.append(value)`; aliases see it |
| Rebind enclosing state | `nonlocal name`; binding must already exist |
| Rebind module state | `global name`; shared within that process |
| Independent request defaults | `None`, then create state inside the call |
| Preserve caller's string history | `list(history)` before appending |
| Extend function knowledge | [Functions module](../01-functions/README.md) |
