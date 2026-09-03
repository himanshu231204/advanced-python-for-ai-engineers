# 24 — Performance & Memory

**Level:** 4 (Deep Python) | **Status:** ✅ Written

Understanding references, mutability, and the memory model explains subtle bugs in shared
agent state and large data pipelines. This module also covers Python's memory management
(reference counting + cyclic GC) and the basics of measuring where time actually goes,
instead of guessing.

---

## 1. What is it?

Every Python variable is a reference to an object living somewhere in memory -- not a box
holding a value directly. Assignment, function arguments, and list elements all copy the
*reference*, never the underlying object. CPython manages memory primarily via reference
counting, with a separate garbage collector to catch reference cycles that counting alone
can't free.

## 2. Why does it exist?

```text
🔥 High ROI
```

Nearly every "spooky action at a distance" bug -- a function that mysteriously mutates its
caller's data, two variables that seem linked when they shouldn't be -- comes down to
misunderstanding that Python passes references, not copies. This is *especially* common with
shared agent/session state, where one branch of conversation history accidentally shares (and
corrupts) another's.

## 3. 💡 Mental Model

```text
a = [1, 2, 3]
b = a          # `b` is another NAME for the SAME object -- no copy
b.append(4)    # mutates the one object both names point to
a              # -> [1, 2, 3, 4] -- `a` "changed" too, because there was only ever one list
```

## 4. Syntax

```python
a is b          # True if a and b reference the SAME object
a == b          # True if a and b are considered equal (can be different objects)
id(a)           # a unique identifier for the object a currently references

import copy
copy.copy(x)      # shallow copy -- new outer container, SAME nested objects
copy.deepcopy(x)  # deep copy -- recursively independent, nothing shared

import gc
gc.collect()      # force a cyclic-garbage-collection pass

import weakref
weakref.ref(obj)  # a reference that does NOT keep `obj` alive by itself

import cProfile, pstats
cProfile.run("my_function()")  # profile where time is actually spent
```

## 5. Minimal Example

```python
a = [1, 2, 3]
b = a
b.append(4)
print(a)  # [1, 2, 3, 4]
```

## 6. What happens internally?

```text
n1, n2 = Node("n1"), Node("n2")
n1.other = n2
n2.other = n1
del n1, n2
        │
        ▼
each Node's refcount drops, but NEVER reaches zero -- n1 is still
referenced by n2.other, and n2 is still referenced by n1.other
        │
        ▼
refcounting alone can NEVER free this cycle; the objects are unreachable
from your code but still "alive" in memory
        │
        ▼
gc.collect() (or Python's automatic periodic cycle detection) walks the
object graph, finds groups of objects only reachable from EACH OTHER
(not from anywhere else), and frees them
```

## 7. Comparison: Shallow Copy vs Deep Copy

| | `copy.copy` (shallow) | `copy.deepcopy` (deep) |
|---|---|---|
| Outer container | new object | new object |
| Nested mutable objects | SHARED with the original | fully independent copies |
| Cost | cheap | more expensive -- recursive |
| AI use case | rarely enough on its own for nested state | branching/forking agent conversation state safely |

## 8. 🎯 AI Engineering Use Case

Forking a conversation into two independent branches (to explore two different next steps)
needs a deep copy -- a shallow copy would leave both branches silently sharing (and
corrupting) the same underlying message list.

### Example A — Tiny

```python
a = [1, 2, 3]
b = a
b.append(4)  # also changes what `a` sees -- same object
```

### Example B — Practical

```python
def add_step(history: list[str], step: str) -> list[str]:
    return [*history, step]  # returns a NEW list, doesn't mutate the caller's
```

### Example C — AI Engineering

```python
import copy

branch_a = conversation_state           # NOT a fork -- same object
branch_b = copy.deepcopy(conversation_state)  # a genuinely independent fork

branch_b["messages"].append("what if we tried X instead?")
# branch_a["messages"] is completely untouched
```

Full runnable version: [`examples/shallow_vs_deep_copy.py`](examples/shallow_vs_deep_copy.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
DEEP COPY
✅ Good for:
- forking/branching mutable state that must NOT be shared afterward
- protecting a caller's data from being mutated by a function it calls

❌ Avoid when:
- the data is immutable anyway (deep-copying a tuple of strings buys nothing)
- performance-sensitive code copies large structures unnecessarily --
  a shallow copy (or no copy at all) may be sufficient if nothing nested
  will actually be mutated

BETTER ALTERNATIVE
Reach for immutable data (tuples, frozen dataclasses, frozensets) where
possible -- there's no aliasing bug possible if nothing can be mutated
in the first place.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — a function silently mutating its caller's argument**

```python
# WRONG -- the caller almost certainly didn't expect their own list to change.
def add_step(history: list[str], step: str) -> list[str]:
    history.append(step)
    return history
```

```python
# BETTER -- return a new list, leave the caller's untouched
def add_step(history: list[str], step: str) -> list[str]:
    return [*history, step]
```

Runnable proof: [`examples/mutability_and_aliasing.py`](examples/mutability_and_aliasing.py)

**Mistake 2 — assuming a shallow copy is enough for nested mutable data**

```python
# WRONG -- copy.copy only duplicates the OUTER dict; the nested list is
# still the SAME object, so mutating it affects "both" copies.
forked = copy.copy(state)
forked["messages"].append("new branch")  # also visible in the original!
```

```python
# BETTER -- deepcopy for genuinely independent nested structures
forked = copy.deepcopy(state)
```

Runnable proof: [`examples/shallow_vs_deep_copy.py`](examples/shallow_vs_deep_copy.py)

**Mistake 3 — guessing at a performance bottleneck instead of measuring it**

```python
# WRONG -- "I think the sum() call is slow" without evidence wastes time
# optimizing the wrong thing.
```

```python
# BETTER -- profile first, then optimize what the data actually shows
import cProfile
cProfile.run("embed_documents(documents)")
```

Runnable proof, with real profiler output identifying the actual hot function:
[`examples/profiling_basics.py`](examples/profiling_basics.py)

## 11. ⚡ Quick Tricks

```python
# Check whether two names point to the SAME object
a is b
```

```python
# Force a cyclic-garbage-collection pass (rarely needed manually)
import gc
gc.collect()
```

```python
# A reference that doesn't keep an object alive -- useful for caches
import weakref
ref = weakref.ref(obj)
```

```python
# Quick profiling of a single call
import cProfile
cProfile.run("my_function()")
```

## 12. Performance Considerations

- `copy.deepcopy` is meaningfully more expensive than `copy.copy` for large or deeply nested
  structures -- use it only when genuine independence is actually needed, not by default
  "just in case."
- Reference counting adds a small overhead to every object reference/dereference, but is
  what makes CPython's memory reclamation prompt and predictable (an object is freed the
  instant nothing references it, rather than waiting for a garbage collection pass).

## 13. 🎤 Interview Questions

**Q: Generator vs list -- when would memory usage differ? (a recap tying back to module 02)**
A: A list materializes every element in memory at once; a generator holds only its current
position and local state, producing values lazily. For a large or unbounded sequence, a
generator can use orders of magnitude less memory -- the same underlying reference/object
model applies to both, but a generator simply never creates most of the objects a list would.

**Q: Why doesn't reference counting alone free a reference cycle?**
A: Reference counting frees an object the instant its count reaches zero. In a cycle (A
refers to B, B refers back to A), each object is still referenced by the other, so neither
count ever reaches zero, even once nothing outside the cycle refers to either of them. A
separate cyclic garbage collector is needed to detect and free such unreachable cycles.

**Q: What's the difference between `is` and `==`?**
A: `is` checks object identity -- whether two references point to the exact same object in
memory. `==` checks equality, which can be true for two distinct objects with the same
value (e.g. two separate list objects both containing `[1, 2, 3]`).

**Q: Why would you deep-copy conversation/agent state before branching it?**
A: Branching means both the original and the new branch need to be mutated independently
going forward. A shallow copy only duplicates the outermost container -- nested mutable
structures (like a message list) remain shared, so mutating one branch would silently
corrupt the other. A deep copy makes the branches genuinely independent.

## 14. 🛠 Mini Exercise

Write a function `fork_state(state: dict) -> dict` that returns a fully independent deep copy
of a nested dict/list structure, then demonstrate that mutating a nested list in the forked
copy does not affect the original.

<details>
<summary>Solution</summary>

```python
import copy


def fork_state(state: dict) -> dict:
    return copy.deepcopy(state)


original = {"steps": [{"action": "search", "result": "found 3 docs"}]}
forked = fork_state(original)

forked["steps"].append({"action": "summarize", "result": "done"})
forked["steps"][0]["result"] = "mutated in the fork"

print(original)  # unchanged -- still just the original single step
print(forked)    # has both the mutated first step AND the new second step
```

</details>

## 15. Real-World Challenge

Extend [`examples/profiling_basics.py`](examples/profiling_basics.py) to compare two
implementations of `fake_embed` -- the current list-comprehension version and a version using
`array.array` instead of a plain list -- profiling both and reporting which one is actually
faster, rather than assuming.

## 16. Cheat Sheet

```text
PERFORMANCE & MEMORY
↓

a is b                  identity: same object?
a == b                  equality: same value?
id(a)                   the object's unique identifier

copy.copy(x)            shallow -- nested mutables still SHARED
copy.deepcopy(x)        deep -- fully independent, recursively

gc.collect()            force a cyclic-GC pass (cycles refcounting can't free)
weakref.ref(obj)        a reference that doesn't keep obj alive

cProfile.run("f()")     measure where time is ACTUALLY spent

WHEN TO USE deepcopy
-> forking/branching mutable state that must not be shared afterward

COMMON MISTAKE
-> a function silently mutating its caller's list/dict argument

AI USE CASE
-> deepcopy conversation state before branching into two independent agent paths
```

---

⬅ Back to [main README](../README.md)
