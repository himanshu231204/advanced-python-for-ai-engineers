# Exercise 2 — Blocking Call Inside an Async Function

**Category:** Broken async code

## Symptom

```text
A start
A end
B start
B end
elapsed: 0.10s
```

Two tasks that should run concurrently instead ran one after the other, and the total time
is the SUM of both delays, not the max. Run [`broken.py`](broken.py) and see it for yourself.

## Root Cause

`time.sleep()` is a blocking call -- it doesn't hand control back to the event loop, it just
freezes the entire thread the loop is running on. `asyncio.gather` can't run `A` and `B`
concurrently if `A`'s `time.sleep(0.05)` refuses to yield control until it's done; `B`
doesn't even get a chance to start until `A`'s sleep finishes.

## Fix

Replace `time.sleep(...)` with `await asyncio.sleep(...)`, which yields control back to the
event loop for the duration, letting other tasks actually run. See [`fixed.py`](fixed.py) --
elapsed time drops to roughly the LONGER of the two delays, not their sum.

## Takeaway

Never call a blocking (synchronous, non-`await`-able) function directly inside an `async
def` -- it stalls the entire event loop, not just the one task. If a blocking call can't be
avoided, run it in a thread pool (`asyncio.to_thread` / `loop.run_in_executor`) instead.
