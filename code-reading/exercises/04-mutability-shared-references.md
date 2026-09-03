# Exercise 4 — Mutability and Shared References

## 1. Snippet

```python
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket

first = add_item("a")
second = add_item("b")
print(first)
print(second)
print(first is second)
```

## 2. Your Prediction

What do `first` and `second` print? Is `first is second` `True` or `False`?

## 3. Answer

```text
['a', 'b']
['a', 'b']
True
```

## 4. Why

- A function's default argument value is evaluated exactly ONCE, when the `def` statement
  runs -- not fresh on every call. `bucket=[]` creates a single list object that becomes the
  default for every call that doesn't pass its own `bucket`.
- Because lists are mutable, `bucket.append(item)` mutates that SAME shared list object every
  time. Both calls end up returning the identical object (`first is second` is `True`), which
  is why `"a"` from the first call is still there when the second call runs.

## 5. 💡 Mental Model

```text
a mutable default argument is created ONCE, at def-time, and shared across every call
that relies on it -- never use `[]`, `{}`, or a mutable object as a default
```
