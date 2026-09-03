# Exercise 6 — Exception Propagation Across Async Boundaries

## 1. Snippet

```python
import asyncio

async def might_fail(n):
    if n == 2:
        raise ValueError(f"bad value: {n}")
    return n * 10

async def main():
    results = await asyncio.gather(
        might_fail(1), might_fail(2), might_fail(3),
        return_exceptions=True,
    )
    print(results)

    try:
        await asyncio.gather(might_fail(1), might_fail(2), might_fail(3))
    except ValueError as exc:
        print(f"raised: {exc}")

asyncio.run(main())
```

## 2. Your Prediction

What does `results` contain in the first `gather` call? What happens in the second call --
does it print all three results, or something else?

## 3. Answer

```text
[10, ValueError('bad value: 2'), 30]
raised: bad value: 2
```

## 4. Why

- `return_exceptions=True` tells `asyncio.gather` to collect an exception raised by any one
  coroutine as a value IN the results list, in that coroutine's original position, rather
  than letting it propagate -- so `might_fail(1)` and `might_fail(3)` still complete and
  contribute their real results, sitting alongside the `ValueError` object for `might_fail(2)`.
- Without `return_exceptions=True` (the default), the first exception raised by ANY of the
  gathered coroutines propagates out of `await asyncio.gather(...)` immediately, as a real
  raised exception -- it's caught by the surrounding `try/except`, and the values that
  `might_fail(1)`/`might_fail(3)` would have returned are simply discarded, never reaching
  the caller.

## 5. 💡 Mental Model

```text
asyncio.gather default : first exception from ANY task propagates, other results are lost
return_exceptions=True : every task's outcome (value OR exception) comes back in the list
```
