# Exercise 5 — Decorator Ordering and `functools.wraps`

## 1. Snippet

```python
def logged(fn):
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper

def shouted(fn):
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        return result.upper()
    return wrapper

@logged
@shouted
def greet(name):
    return f"hello {name}"

print(greet("ai"))
print(greet.__name__)
```

## 2. Your Prediction

What does `greet("ai")` return? What does `greet.__name__` print, and why might that be
surprising?

## 3. Answer

```text
calling wrapper
HELLO AI
wrapper
```

## 4. Why

- Stacked decorators apply BOTTOM-UP: `@shouted` wraps `greet` first, then `@logged` wraps
  the result of that. So calling `greet(...)` actually calls `logged`'s `wrapper`, which
  calls `shouted`'s `wrapper`, which calls the real `greet` and uppercases its result --
  hence `"HELLO AI"`.
- `logged`'s `print(f"calling {fn.__name__}")` prints `"calling wrapper"`, not
  `"calling greet"` -- `fn` there is `shouted`'s inner `wrapper` function, and neither
  `wrapper` was decorated with `functools.wraps`, so it never inherited the original
  function's `__name__`. The same reason `greet.__name__` is `"wrapper"` instead of
  `"greet"` after both decorators are applied -- each decorator silently replaced the
  original function's identity with its own wrapper's.

## 5. 💡 Mental Model

```text
decorators apply bottom-up but are LISTED top-down in source
without @functools.wraps(fn) on every wrapper, __name__/__doc__/introspection
all leak the wrapper's identity instead of the original function's
```
