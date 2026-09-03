# 11 — Protocols & Generics

**Level:** 2 (Production Python) | **Status:** ✅ Written

`Protocol` gives you structural typing so model providers, tools, and retrievers can be
swapped without inheritance -- key for clean AI system abstractions. This module goes past
module 07's light preview into real depth: `@runtime_checkable`, generic classes/functions,
and bounded type parameters -- and ends with the model-provider abstraction pattern used
throughout production AI systems.

> Generic class/function examples in this module use PEP 695 syntax (`class Stack[T]:`),
> which requires **Python 3.12+**. `structural_typing.py` runs on any supported version.

---

## 1. What is it?

`Protocol` defines a type by the methods/attributes an object has (structural typing --
"if it walks like a duck..."), instead of by what it inherits from (nominal typing). Generics
(`class Stack[T]:`, `def first[T](...)`) let a class or function be written once and work
correctly across many concrete types, with a type checker tracking exactly which type is in
use at each call site.

## 2. Why does it exist?

```text
Python Concept
      ↓
Protocol
      ↓
model abstraction
```

An AI system routes through many swappable pieces -- LLM providers, retrievers, tools -- that
all need "the same shape" without necessarily sharing a common base class (especially across
third-party SDKs you don't control). `Protocol` lets you define that shared shape once and
check any object against it, including objects from libraries that have never heard of your
Protocol.

## 3. 💡 Mental Model

```text
Nominal typing (inheritance):  "are you a registered member of this family?"
Structural typing (Protocol):  "do you have the right methods? then you qualify."
```

Generics extend this: `Stack[int]` and `Stack[str]` are the same class, parameterized by
which concrete type flows through it -- like a template a type checker fills in per use.

## 4. Syntax

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...

# Any class with a matching `embed` method satisfies Embedder -- no inheritance.

# Generic class (Python 3.12+ syntax)
class Stack[T]:
    def push(self, item: T) -> None: ...
    def pop(self) -> T: ...

# Generic function (Python 3.12+ syntax)
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

# Bounded type parameter -- T must have whatever HasId requires
class HasId(Protocol):
    id: str

class Repository[T: HasId]:
    def add(self, item: T) -> None:
        self._items[item.id] = item  # valid: every T has .id
```

## 5. Minimal Example

```python
from typing import Protocol

class Greeter(Protocol):
    def greet(self) -> str: ...

class English:
    def greet(self) -> str:
        return "Hello!"

def say_hi(g: Greeter) -> None:
    print(g.greet())

say_hi(English())  # Hello!  -- English never mentions Greeter
```

## 6. What happens internally?

```text
def run_pipeline(provider: ModelProvider, prompt: str) -> str:
    return provider.generate(prompt)
        │
        ▼
at RUNTIME, Python does nothing special here -- it just calls
provider.generate(prompt) like any normal method call
        │
        ▼
the Protocol check happens STATICALLY, by mypy/pyright, which verifies at
type-check time that whatever gets passed as `provider` actually has a
compatible `generate(self, prompt: str) -> str` method
        │
        ▼
@runtime_checkable ADDS an actual runtime check: isinstance(x, Protocol)
becomes possible, but it only checks that the right METHOD NAMES exist --
not that their signatures match
```

## 7. Comparison: Protocol vs Abstract Base Class (ABC) vs Duck Typing

| | Plain duck typing | `Protocol` | `abc.ABC` |
|---|---|---|---|
| Declares a contract? | no, implicit | yes, explicit and checkable | yes, explicit |
| Requires inheritance? | no | no | yes |
| Checked by | nothing, until it breaks at runtime | a type checker (statically) | Python itself, at instantiation |
| Works with 3rd-party classes you don't own? | yes | yes | no (can't retroactively inherit) |
| AI use case | quick scripts | swappable model/tool/retriever abstractions | a plugin system you fully control |

## 8. 🎯 AI Engineering Use Case

A `ModelProvider` protocol lets `run_pipeline` accept a real LLM client, a local echo
implementation, or a fixed fake for tests -- all without any of them inheriting from anything.

### Example A — Tiny

```python
class Greeter(Protocol):
    def greet(self) -> str: ...
```

### Example B — Practical

```python
class Repository[T: HasId]:
    def add(self, item: T) -> None:
        self._items[item.id] = item
```

### Example C — AI Engineering

```python
class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

def run_pipeline(provider: ModelProvider, prompt: str) -> str:
    return provider.generate(prompt)

run_pipeline(OpenAIStyleProvider("gpt-mini"), "hello")
run_pipeline(FakeTestProvider(), "hello")  # a test double, zero setup
```

Full runnable version: [`examples/model_provider_abstraction.py`](examples/model_provider_abstraction.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
PROTOCOLS & GENERICS
✅ Good for:
- swappable provider/tool/retriever abstractions, especially across 3rd-party
  classes you can't make inherit from a shared base
- generic containers/utilities (a typed cache, repository, or queue) reused
  across many concrete types
- bounding a TypeVar when a generic class needs to rely on SOME shared shape

❌ Avoid when:
- there's truly only ever going to be one concrete implementation -- a
  Protocol adds a layer of indirection with no real payoff
- the "generic" logic secretly behaves differently per type anyway (that's
  a sign you need a Protocol dispatch or separate functions, not one generic)

BETTER ALTERNATIVE
Use `abc.ABC` when you own every implementation and actively want to
enforce inheritance (e.g. a plugin system with a required registration
step). Use a Protocol whenever you don't own all the implementations, or
inheritance would be needless ceremony.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — expecting `isinstance()` to work on a `Protocol` without `@runtime_checkable`**

```python
# WRONG -- raises TypeError; a plain Protocol can't be used with isinstance()
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...

isinstance(my_obj, Embedder)  # TypeError: Instance and class checks can only
                               # be used with @runtime_checkable protocols
```

```python
# BETTER
from typing import runtime_checkable

@runtime_checkable
class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...

isinstance(my_obj, Embedder)  # now works
```

Runnable proof: [`examples/structural_typing.py`](examples/structural_typing.py)

**Mistake 2 — assuming `@runtime_checkable` verifies method signatures**

```python
# WRONG ASSUMPTION -- isinstance() only checks that the METHOD NAME exists,
# not that its parameters/return type actually match the Protocol.
class BrokenEmbedder:
    def embed(self) -> str:  # wrong signature entirely
        return "oops"

isinstance(BrokenEmbedder(), Embedder)  # True! -- name matched, signature didn't
```

```python
# BETTER -- rely on a real type checker (mypy/pyright) run in CI to catch
# signature mismatches; @runtime_checkable is a coarse existence check only.
```

**Mistake 3 — reaching for a generic class where a Protocol (or nothing) would do**

```python
# WRONG -- wrapping a single concrete type in a needless generic adds
# ceremony with no actual reuse benefit.
class StringBox[T]:
    def __init__(self, value: T) -> None: ...
# ...only ever instantiated as StringBox[str] everywhere in the codebase
```

```python
# BETTER -- if there's truly one concrete type in practice, just use it directly
class StringBox:
    def __init__(self, value: str) -> None: ...
```

## 11. ⚡ Quick Tricks

```python
# Structural check at runtime
@runtime_checkable
class Sized(Protocol):
    def __len__(self) -> int: ...
```

```python
# Modern generic class -- no typing.Generic/TypeVar import needed (3.12+)
class Stack[T]: ...
```

```python
# Bound a type parameter to a Protocol so the generic body can rely on it
class Repository[T: HasId]: ...
```

```python
# A quick fake/test double that satisfies a Protocol with zero setup
class FakeTestProvider:
    def generate(self, prompt: str) -> str:
        return "fixed test response"
```

## 12. Performance Considerations

- Protocols have zero runtime cost by themselves -- `isinstance()` checks against a
  `@runtime_checkable` protocol do real work (checking each required attribute exists), but
  most Protocol usage is purely static and costs nothing at runtime.
- Generics are a type-checking-time concept; the generated bytecode for `Stack[int]` and
  `Stack[str]` is identical -- there's no runtime specialization or overhead per type
  parameter.

## 13. 🎤 Interview Questions

**Q: What's the difference between structural typing (`Protocol`) and nominal typing
(inheritance/ABC)?**
A: Nominal typing checks whether a class explicitly declares itself part of a type's family
(via inheritance). Structural typing checks whether an object simply *has* the right
shape (methods/attributes) -- Python calls this "duck typing," and `Protocol` makes it
checkable by static tools without requiring any inheritance relationship.

**Q: Why would you use `Protocol` instead of an abstract base class for a model-provider
abstraction?**
A: Because different LLM SDKs are third-party classes you don't control -- you can't make
`OpenAIClient` inherit from your own `ModelProvider` ABC. A `Protocol` lets any of those
classes satisfy your abstraction automatically, as long as they have a compatible method,
with zero changes to the SDK's own code.

**Q: What does `@runtime_checkable` actually check, and what does it NOT check?**
A: It lets `isinstance()`/`issubclass()` be used against a Protocol, checking that the object
has attributes/methods with the required *names*. It does **not** check method signatures
(parameter types, return types) -- a method with the right name but a completely wrong
signature still passes the `isinstance()` check.

**Q: What's a bounded TypeVar, and why would a generic class need one?**
A: A bounded type parameter (`class Repository[T: HasId]`) restricts what concrete types `T`
can be to those satisfying some constraint (here, having an `id` attribute). This lets the
generic class's body safely use `item.id` for any valid `T`, because a type checker
guarantees every substitution satisfies that bound.

## 14. 🛠 Mini Exercise

Define a Protocol `Scorable` with a `score(self) -> float` method, and a generic function
`best[T: Scorable](items: list[T]) -> T | None` that returns the item with the highest score
(or `None` for an empty list), using `max()` with a `key=`.

<details>
<summary>Solution</summary>

```python
from typing import Protocol


class Scorable(Protocol):
    def score(self) -> float: ...


def best[T: Scorable](items: list[T]) -> T | None:
    if not items:
        return None
    return max(items, key=lambda item: item.score())


class SearchResult:
    def __init__(self, title: str, relevance: float) -> None:
        self.title = title
        self.relevance = relevance

    def score(self) -> float:
        return self.relevance

    def __repr__(self) -> str:
        return f"SearchResult({self.title!r}, {self.relevance})"


results = [SearchResult("A", 0.4), SearchResult("B", 0.9)]
print(best(results))  # SearchResult('B', 0.9)
print(best([]))  # None
```

</details>

## 15. Real-World Challenge

Extend [`examples/model_provider_abstraction.py`](examples/model_provider_abstraction.py)
with a generic `Cache[K, V]` class (bounded so `K` must be hashable) that wraps any
`ModelProvider`-satisfying object, caching `generate()` results by prompt so repeated calls
with the same prompt skip the underlying provider entirely -- a preview of the real caching
pattern in `16-caching`.

## 16. Cheat Sheet

```text
PROTOCOLS & GENERICS
↓

class P(Protocol):              class Stack[T]:              class Repo[T: HasId]:
    def method(self) -> X: ...      def push(self, x: T): ...    def add(self, item: T): ...

@runtime_checkable        # enables isinstance() against a Protocol (name-only check)

WHEN TO USE
-> swappable provider/tool abstractions; generic containers reused across types

COMMON MISTAKE
-> assuming @runtime_checkable verifies method SIGNATURES (it only checks names exist)

AI USE CASE
-> class ModelProvider(Protocol): def generate(self, prompt: str) -> str: ...
   # swap real/local/fake providers with zero inheritance
```

---

⬅ Back to [main README](../README.md)
