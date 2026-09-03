# Exercise 1 — Missing `await`

**Category:** Broken async code

## Symptom

```text
result: <coroutine object fetch_answer at 0x...>
type: <class 'coroutine'>
/usr/lib/python3.11/asyncio/events.py:84: RuntimeWarning: coroutine 'fetch_answer' was never awaited
```

Run [`broken.py`](broken.py) and see it for yourself.

## Root Cause

`fetch_answer()` is an `async def` function -- calling it doesn't run its body at all, it
just creates and returns a coroutine *object*. That object only actually executes when it's
awaited (or scheduled as a task). Without `await`, `result` is the coroutine itself, never
the integer it was supposed to produce -- and Python's own warning system flags it, because
an un-awaited coroutine is almost always a bug.

## Fix

Add the missing `await`: `result = await fetch_answer()`. See [`fixed.py`](fixed.py).

## Takeaway

If a variable holding what should be a value prints as `<coroutine object ...>`, the fix is
almost always: find the call and add `await` in front of it.
