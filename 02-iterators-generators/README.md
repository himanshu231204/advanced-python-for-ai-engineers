# 02 — Iterators & Generators

**Level:** 1 (Modern Python Core) | **Status:** ✅ Written

Generators are how Python streams data without loading everything into memory -- the same
idea behind token streaming, paginated API results, and lazy data pipelines in AI systems.
Understanding the iterator protocol underneath `for` loops is also what makes `async for` and
async generators (`04-async-generators-streaming`) click later.

---

## 1. What is it?

An **iterator** is any object with `__next__()` (and `__iter__()` returning itself) that
produces one value at a time until it raises `StopIteration`. A **generator** is the easy way
to create an iterator: a function that uses `yield` instead of `return`, pausing its state
between values instead of computing everything up front.

## 2. Why does it exist?

Some data is too large to hold in memory at once (a huge dataset, an infinite stream, tokens
from an LLM as they're produced). Iterators let you process a sequence **one item at a time**,
computing the next value only when it's asked for -- this is called **lazy evaluation**.

## 3. 💡 Mental Model

```text
list        -> the whole cake, baked and sitting on the counter
iterator    -> a cake that gets baked one slice at a time, only when you ask for a slice
```

A `for` loop over anything is really Python calling `iter(obj)` once, then `next(...)`
repeatedly until it catches `StopIteration`.

## 4. Syntax

```python
# Iterator protocol (manual)
class Countdown:
    def __init__(self, n: int) -> None:
        self.n = n

    def __iter__(self) -> "Countdown":
        return self

    def __next__(self) -> int:
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1


# Generator function (the easy way)
def countdown(n: int):
    while n > 0:
        yield n
        n -= 1

# Generator expression
squares = (x * x for x in range(10))

# yield from -- delegate to another iterable/generator
def combined():
    yield from countdown(3)
    yield from countdown(2)
```

## 5. Minimal Example

```python
def countdown(n: int):
    while n > 0:
        yield n
        n -= 1

for i in countdown(3):
    print(i)  # 3  2  1
```

## 6. What happens internally?

```text
gen = countdown(3)          # nothing runs yet -- a generator object is created
next(gen)  -> 3              # runs until the first `yield`, pauses, returns 3
next(gen)  -> 2              # resumes right after `yield`, runs to the next one
next(gen)  -> 1
next(gen)  -> StopIteration  # function falls off the end -> loop stops
```

A generator function's body doesn't execute at call time -- calling it just builds a
generator object. Execution only happens as the object is iterated, and it resumes exactly
where it last paused (all local variables are preserved).

## 7. Comparison: List vs Generator vs Custom Iterator

| | `list` | Generator (`yield`) | Custom Iterator (`__next__`) |
|---|---|---|---|
| Memory | holds all items at once | holds one item + paused state | holds one item + whatever state you track |
| Reusable? | yes, any number of times | no -- exhausted after one full pass | depends on your implementation |
| When values compute | all up front | lazily, on each `next()` | lazily, on each `next()` |
| Boilerplate | none | minimal (`yield`) | a full class with `__iter__`/`__next__` |
| AI use case | small, fixed, reusable data | streaming tokens, paginated results | rare -- only when you need extra state/methods beyond iteration |

## 8. 🎯 AI Engineering Use Case

```text
LLM completion
 ↓
tokens produced one at a time
 ↓
generator yields each token as it's ready
 ↓
consumer (terminal, API response, UI) renders incrementally
```

This is the *synchronous* shape of LLM token streaming. Module `04` does the same thing with
`async def` + `yield` so it works inside an `await`-based event loop (e.g. FastAPI + SSE), but
the core idea -- produce one value, pause, resume on demand -- is identical.

### Example A — Tiny

```python
def countdown(n: int):
    while n > 0:
        yield n
        n -= 1
```

### Example B — Practical

```python
def paginate(items: list[str], page_size: int):
    for start in range(0, len(items), page_size):
        yield items[start : start + page_size]
```

### Example C — AI Engineering

```python
def stream_tokens(text: str):
    for word in text.split(" "):
        yield word + " "
```

Full runnable version: [`examples/token_stream.py`](examples/token_stream.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
GENERATORS
✅ Good for:
- streaming data you don't want (or can't) hold in memory at once
- pipelines where each stage should start producing output before the previous
  stage finishes (LLM tokens, paginated API results, log processing)
- infinite or very large sequences

❌ Avoid when:
- you need to iterate over the same data multiple times (a generator is single-use)
- you need random access (`items[5]`) or `len()` -- generators support neither
- the dataset is small and fits comfortably in memory -- a list is simpler and reusable

BETTER ALTERNATIVE
Use a list (or tuple) when you need to iterate more than once, need indexing, or the
data is small enough that "lazy" buys you nothing.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — trying to reuse an exhausted generator**

```python
# WRONG -- a generator can only be iterated once
gen = (x * 2 for x in range(3))
print(list(gen))  # [0, 2, 4]
print(list(gen))  # []  <- silently empty, not an error!
```

```python
# BETTER -- store the source, create a fresh generator each time you need one
def doubled(n: int):
    return (x * 2 for x in range(n))

print(list(doubled(3)))  # [0, 2, 4]
print(list(doubled(3)))  # [0, 2, 4]  <- fresh generator each call
```

**Mistake 2 — accidentally materializing a huge generator into a list**

```python
# WRONG -- defeats the entire purpose of streaming; loads everything into memory
tokens = list(stream_tokens(giant_llm_response))
for t in tokens:
    render(t)
```

```python
# BETTER -- iterate the generator directly, one token at a time
for t in stream_tokens(giant_llm_response):
    render(t)
```

**Mistake 3 — calling `next()` on an exhausted generator and not catching `StopIteration`**

```python
# WRONG -- raises StopIteration and crashes the caller if you assumed more items exist
gen = countdown(0)
value = next(gen)  # StopIteration!
```

```python
# BETTER -- provide a default, or iterate with a for-loop which handles this for you
gen = countdown(0)
value = next(gen, None)
if value is None:
    print("nothing left")
```

## 11. ⚡ Quick Tricks

```python
for item in iterator:
    ...
```

```python
# Get the next value with a fallback instead of risking StopIteration
value = next(my_generator, "default")
```

```python
# Chain multiple iterables lazily without concatenating lists
from itertools import chain
for x in chain(list_a, list_b, generator_c):
    ...
```

```python
# Delegate to sub-generators cleanly
def combined():
    yield from source_a()
    yield from source_b()
```

## 12. Performance Considerations

- A generator expression is created in near-constant time regardless of the underlying
  range's size -- see [`examples/generator_expressions.py`](examples/generator_expressions.py),
  where a 1,000,000-item list comprehension is ~8 MB while the equivalent generator is ~200
  bytes.
- Generators trade memory for the inability to know length ahead of time (`len()` doesn't
  work) or re-iterate -- pick based on which constraint actually matters for the use case.

## 13. 🎤 Interview Questions

**Q: What's the difference between an iterable and an iterator?**
A: An iterable is anything `iter()` can be called on (lists, generators, custom objects
implementing `__iter__`). An iterator is the stateful object that actually produces values via
`__next__()`. Every iterator is iterable (its `__iter__` returns itself), but not every
iterable is an iterator (a list is iterable but isn't itself an iterator).

**Q: Generator vs list — when would memory usage differ, and by how much?**
A: A list holds every element in memory simultaneously; a generator holds only its current
position and local state. For a million computed values, a list might use megabytes while a
generator uses a couple hundred bytes -- the difference grows with the size of the sequence,
not with anything about the generator itself.

**Q: What does `yield from` actually do?**
A: It delegates iteration to a sub-iterable, re-yielding each of its values as if the outer
generator had yielded them directly -- equivalent to (but more efficient and correct than)
manually writing `for x in sub_iterable: yield x`, and it also correctly forwards `send()`,
`throw()`, and the sub-generator's return value.

**Q: Why can't you call `next()` on a generator twice and get the same value?**
A: A generator's execution state is mutated by each `next()` call -- it resumes past the
`yield` it stopped at and runs until the next one. There's no way to "rewind" without creating
a brand-new generator from scratch.

## 14. 🛠 Mini Exercise

Write a generator `batched(items: list, size: int)` that yields successive lists of at most
`size` items from `items` (the last batch may be smaller). Then write a generator
`take(iterable, n)` that yields only the first `n` values from any iterable, stopping early
even if the source has more.

<details>
<summary>Solution</summary>

```python
from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def batched(items: list[T], size: int) -> Iterator[list[T]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def take(iterable: Iterable[T], n: int) -> Iterator[T]:
    it = iter(iterable)
    for _ in range(n):
        try:
            yield next(it)
        except StopIteration:
            return
```

</details>

## 15. Real-World Challenge

Extend [`examples/yield_from.py`](examples/yield_from.py)'s `hybrid_search` so it accepts an
arbitrary list of search-generator functions (not just two hardcoded ones) and yields their
combined results in the order the list was given, using `yield from` in a loop.

## 16. Cheat Sheet

```text
ITERATORS & GENERATORS
↓

class C:                    def gen():                (x for x in range(n))
    def __iter__(self): ...     while cond:            generator expression --
    def __next__(self): ...        yield value         lazy, near-zero memory

WHEN TO USE
-> streaming data, large/infinite sequences, one-pass pipelines

COMMON MISTAKE
-> reusing an exhausted generator (silently returns nothing, no error)

AI USE CASE
-> stream_tokens(llm_response)  # yield one token at a time instead of returning it all
```

---

⬅ Back to [main README](../README.md)
