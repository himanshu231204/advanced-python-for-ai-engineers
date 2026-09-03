# Exercise 1 — Generator Exhaustion & Evaluation Order

## 1. Snippet

Read this. Don't run it yet.

```python
def gen():
    print("start")
    yield 1
    print("middle")
    yield 2
    print("end")

g = gen()
values = [next(g), next(g)]
print(values)

squares = (x * x for x in range(3))
total = sum(squares) + sum(squares)
print(total)
```

## 2. Your Prediction

Write down, before scrolling:
- The exact order of every printed line.
- What `total` ends up being.

## 3. Answer

```text
start
middle
[1, 2]
5
```

## 4. Why

- A generator function's body doesn't run at all when you call `gen()` -- it runs only as
  each `next()` pulls a value, pausing right at each `yield`. The first `next(g)` runs up to
  and including `print("start")` / `yield 1`; the second runs from just after that yield up
  to `print("middle")` / `yield 2`. `"end"` never prints because nothing asks for a third
  value.
- `squares` is a generator expression -- a single-use iterator, not a list. The first
  `sum(squares)` fully consumes it (`0 + 1 + 4 = 5`). By the second `sum(squares)`, the
  generator is already exhausted, so it immediately raises `StopIteration` internally and
  `sum` treats that as "no more items" -- yielding `0`. Total: `5 + 0 = 5`.

## 5. 💡 Mental Model

```text
a generator's code runs LAZILY, one yield at a time, only when pulled
a generator can be consumed ONCE -- iterating it again gives nothing, not an error
```
