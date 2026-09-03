# 10 — Advanced OOP & Magic Methods

**Level:** 4 (Deep Python) | **Status:** ✅ Written

Understanding dunder ("double underscore") methods explains how iteration, callables, and
context managers work under the hood -- useful when building custom agent/tool abstractions.
`__iter__`/`__next__` (module 02), `__aiter__`/`__anext__` (module 04), and `__enter__`/
`__exit__` (module 05) were already covered where they were most useful; this module adds
`__call__`, descriptors, and operator overloading, then ties all of them together as one
family of protocols.

---

## 1. What is it?

Dunder methods are special methods (`__init__`, `__call__`, `__add__`, ...) that Python calls
automatically in response to syntax or built-in functions, rather than you calling them
directly. `obj(x)` calls `obj.__call__(x)`; `a + b` calls `a.__add__(b)`; `for x in obj` drives
`obj.__iter__()`/`__next__()`.

## 2. Why does it exist?

Without dunder methods, every custom object would need its own bespoke API (`obj.call(x)`,
`obj.add(b)`, `obj.get_next()`) instead of working with Python's built-in syntax. Dunders let
custom classes integrate seamlessly with the language itself -- `+`, `for`, `with`, `()` all
just work, as long as the right dunder is implemented.

## 3. 💡 Mental Model

```text
obj(x)        -> obj.__call__(x)
a + b         -> a.__add__(b)
a == b        -> a.__eq__(b)
for x in obj: -> obj.__iter__() then repeated obj.__next__()
with obj:     -> obj.__enter__() ... obj.__exit__(...)
```

Whenever a piece of Python syntax "just works" on a custom object, there's a dunder method
behind it -- syntax is sugar for a method call Python makes on your behalf.

## 4. Syntax

```python
class Multiplier:
    def __init__(self, factor: int) -> None:
        self.factor = factor

    def __call__(self, value: int) -> int:   # makes instances callable
        return value * self.factor

class PositiveNumber:                          # a descriptor
    def __set_name__(self, owner, name):
        self._name = f"_{name}"
    def __get__(self, instance, owner):
        return getattr(instance, self._name)
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("must be positive")
        setattr(instance, self._name, value)

class Vector:                                   # operator overloading
    def __add__(self, other): ...
    def __eq__(self, other): ...
    def __repr__(self): ...
```

## 5. Minimal Example

```python
class Multiplier:
    def __init__(self, factor: int) -> None:
        self.factor = factor
    def __call__(self, value: int) -> int:
        return value * self.factor

double = Multiplier(2)
print(double(5))  # 10
```

## 6. What happens internally?

```text
double(5)
        │
        ▼
Python sees `double` is being CALLED like a function
        │
        ▼
it looks up type(double).__call__ (NOT an instance attribute lookup --
dunder methods are always looked up on the class, a detail that matters
for edge cases but rarely bites you in normal code)
        │
        ▼
runs Multiplier.__call__(double, 5) -> returns 10
```

## 7. Comparison: The Dunder Method Family

| Protocol | Dunders | Drives | Covered in |
|---|---|---|---|
| Callable | `__call__` | `obj(...)` | this module |
| Iterator | `__iter__`, `__next__` | `for x in obj`, `next(obj)` | `02-iterators-generators` |
| Async iterator | `__aiter__`, `__anext__` | `async for x in obj` | `04-async-generators-streaming` |
| Context manager | `__enter__`, `__exit__` | `with obj:` | `05-context-managers` |
| Descriptor | `__get__`, `__set__`, `__set_name__` | attribute access on ANOTHER class | this module |
| Operator overload | `__add__`, `__eq__`, `__repr__`, ... | `+`, `==`, `print()` | this module |

## 8. 🎯 AI Engineering Use Case

A callable `Tool` base class lets tool objects be invoked exactly like functions
(`tool(**arguments)` -- the same shape an LLM's tool-call dispatch already expects) while
still carrying state (call counts, config, cached clients) that a plain function can't.

### Example A — Tiny

```python
class Multiplier:
    def __call__(self, value: int) -> int:
        return value * 2
```

### Example B — Practical

```python
class PositiveNumber:  # a reusable validated-attribute descriptor
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("must be positive")
        ...
```

### Example C — AI Engineering

```python
class Tool:
    def __call__(self, **kwargs: object) -> str:
        self.call_count += 1
        return self.run(**kwargs)

class SearchTool(Tool):
    def run(self, *, query: str, top_k: int = 3) -> str:
        return f"top {top_k} results for {query!r}"

search = SearchTool()
search(query="advanced oop")  # calls the instance like a function, tracks state
```

Full runnable version: [`examples/callable_tool_registry.py`](examples/callable_tool_registry.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
MAGIC METHODS
✅ Good for:
- making a stateful object usable with natural Python syntax (callable
  tools, custom iterators, context-managed resources)
- descriptors for reusable validation/computed-attribute logic shared
  across many classes

❌ Avoid when:
- overloading an operator in a way that surprises readers (e.g. `+` that
  doesn't mean "combine" in any intuitive sense)
- reaching for a descriptor when a plain `@property` (simpler, one class
  only) would do

BETTER ALTERNATIVE
Use `@property` for one-off computed/validated attributes on a single
class. Reach for a full descriptor only when the SAME validation logic
needs to be reused across multiple classes/attributes.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — implementing `__eq__` without handling non-matching types**

```python
# WRONG -- crashes (AttributeError) instead of returning False when
# compared against something that isn't a Vector.
def __eq__(self, other):
    return self.x == other.x and self.y == other.y

Vector(1, 2) == "not a vector"  # AttributeError: 'str' object has no attribute 'x'
```

```python
# BETTER -- return NotImplemented so Python falls back correctly
def __eq__(self, other):
    if not isinstance(other, Vector):
        return NotImplemented
    return self.x == other.x and self.y == other.y
```

**Mistake 2 — forgetting `__set_name__` and hardcoding a descriptor's storage name**

```python
# WRONG -- every instance using this descriptor for ANY attribute name
# collides on the same "_value" storage slot.
class PositiveNumber:
    def __set__(self, instance, value):
        instance._value = value  # hardcoded name -- breaks with multiple attributes
```

```python
# BETTER -- __set_name__ tells the descriptor what it's actually named,
# so each attribute gets its own storage slot.
class PositiveNumber:
    def __set_name__(self, owner, name):
        self._name = f"_{name}"
    def __set__(self, instance, value):
        setattr(instance, self._name, value)
```

Runnable proof: [`examples/descriptors.py`](examples/descriptors.py)

**Mistake 3 — overloading operators for non-obvious behavior**

```python
# WRONG -- `+` on a Tool registry that actually means "register a new
# tool" is surprising; nobody expects `+` to have side effects like this.
class ToolRegistry:
    def __add__(self, tool):
        self.tools.append(tool)  # a side-effecting "add" is a bad use of __add__
        return self
```

```python
# BETTER -- use a clearly-named method for anything with side effects or
# non-obvious meaning; save operator overloading for genuinely intuitive
# cases (adding two vectors, concatenating two sequences).
class ToolRegistry:
    def register(self, tool):
        self.tools.append(tool)
        return self
```

## 11. ⚡ Quick Tricks

```python
# Check if something is callable before calling it dynamically
if callable(obj):
    obj()
```

```python
# __repr__ vs __str__: __repr__ is for developers/debugging (aim for
# something that could recreate the object); __str__ is for end users.
def __repr__(self) -> str:
    return f"Vector({self.x}, {self.y})"
```

```python
# A class combining multiple protocols at once -- perfectly normal
class Resource:
    def __enter__(self): ...
    def __exit__(self, *exc): ...
    def __iter__(self): ...
    def __next__(self): ...
```

## 12. Performance Considerations

- Dunder method lookups go through the class, not the instance -- this is a CPython
  implementation detail that makes them fast and consistent, but means you can't override a
  dunder by setting it directly on an instance (`obj.__call__ = fn` won't make `obj()` work).
- Descriptors add one extra attribute-access hop compared to a plain instance attribute --
  negligible unless you're accessing it in an extremely hot loop.

## 13. 🎤 Interview Questions

**Q: What's the difference between `__repr__` and `__str__`?**
A: `__repr__` is meant for developers -- ideally unambiguous enough to help debugging, often
written to look like valid Python that could reconstruct the object. `__str__` is meant for
end users and is what `print()` and `str()` use if defined; if `__str__` is missing, Python
falls back to `__repr__`.

**Q: Why should `__eq__` return `NotImplemented` instead of `False` for an incompatible
type?**
A: Returning `NotImplemented` tells Python "I don't know how to compare these -- try the
other object's `__eq__`, or fall back to identity comparison" rather than asserting a
definite (and possibly wrong) answer. Returning `False` directly would incorrectly claim two
objects of totally different types are known to be unequal by this class's logic, even when
this class has no idea how to compare them.

**Q: What problem do descriptors solve that `@property` doesn't?**
A: `@property` defines get/set logic for one specific attribute on one specific class.
Descriptors let you write that logic ONCE, in a separate reusable class, and attach it to
many different attributes across many different classes -- exactly like the `PositiveNumber`
descriptor being reused for any "must be positive" attribute.

**Q: How does `obj()` actually dispatch to `__call__`?**
A: Python looks up `__call__` on `type(obj)` (the class), not on the instance itself, and
calls it as `type(obj).__call__(obj, ...)`. This is true of all dunder methods, which is why
assigning `__call__` directly onto an instance has no effect on whether that instance is
callable.

## 14. 🛠 Mini Exercise

Write a class `Accumulator` that is callable (`__call__(self, value: int) -> int`), adding
`value` to an internal running total and returning the new total each time it's called. Also
implement `__repr__` so `print(acc)` shows the current total clearly.

<details>
<summary>Solution</summary>

```python
class Accumulator:
    def __init__(self) -> None:
        self.total = 0

    def __call__(self, value: int) -> int:
        self.total += value
        return self.total

    def __repr__(self) -> str:
        return f"Accumulator(total={self.total})"


acc = Accumulator()
print(acc(5))   # 5
print(acc(10))  # 15
print(acc)      # Accumulator(total=15)
```

</details>

## 15. Real-World Challenge

Extend [`examples/callable_tool_registry.py`](examples/callable_tool_registry.py) with a
`ToolRegistry` class that supports `registry["search_docs"]` (via `__getitem__`) to fetch a
registered tool by name, and `len(registry)` (via `__len__`) to report how many tools are
registered -- practice recognizing which dunder corresponds to which piece of syntax.

## 16. Cheat Sheet

```text
MAGIC METHODS
↓

__call__(self, *a, **kw)     obj(...)          callable tool/decorator objects
__get__/__set__               attribute access   reusable validated attributes (descriptors)
__set_name__                  descriptor setup    knows its own attribute name
__add__/__eq__/__repr__       +, ==, print()      operator overloading (use sparingly)
__iter__/__next__             for x in obj        see 02-iterators-generators
__aiter__/__anext__           async for x in obj  see 04-async-generators-streaming
__enter__/__exit__            with obj:           see 05-context-managers

WHEN TO USE
-> making a stateful object work with natural, expected Python syntax

COMMON MISTAKE
-> __eq__ raising instead of returning NotImplemented for an unrelated type

AI USE CASE
-> a callable Tool class: tool(**arguments) works like a function call but keeps state
```

---

⬅ Back to [main README](../README.md)
