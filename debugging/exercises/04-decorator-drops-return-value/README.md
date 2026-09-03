# Exercise 4 — Decorator Silently Drops the Return Value

**Category:** Broken decorators

## Symptom

```text
calling add
result: None
```

`add(2, 3)` should be `5`, not `None`. Run [`broken.py`](broken.py) and see it for yourself.

## Root Cause

The `wrapper` function calls `fn(*args, **kwargs)` but never `return`s the result -- a
function with no explicit `return` (or a bare `return`) always evaluates to `None`. Every
call through this decorator silently discards whatever the real function computed, even
though `@wraps(fn)` correctly preserves the function's name and metadata -- `wraps` doesn't
help here, because the bug is in the wrapper's control flow, not its identity.

## Fix

Add the missing `return` in front of `fn(*args, **kwargs)`. See [`fixed.py`](fixed.py).

## Takeaway

Every wrapper function in a decorator MUST explicitly `return` whatever the wrapped function
returns (or a deliberately transformed version of it) -- forgetting the `return` is an easy,
easy-to-miss mistake because the decorator still "runs" without raising any error at all.
