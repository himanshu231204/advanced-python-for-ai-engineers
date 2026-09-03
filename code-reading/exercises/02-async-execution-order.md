# Exercise 2 — Async/Await Execution Order

## 1. Snippet

```python
import asyncio

async def worker(name, delay):
    print(f"{name} start")
    await asyncio.sleep(delay)
    print(f"{name} end")

async def main():
    print("main start")
    task_a = asyncio.create_task(worker("A", 0.02))
    task_b = asyncio.create_task(worker("B", 0.01))
    print("main before await")
    await task_a
    await task_b
    print("main done")

asyncio.run(main())
```

## 2. Your Prediction

Write down the exact order of every printed line -- pay attention to whether `task_a` or
`task_b`'s "start" prints first, and which one's "end" prints first.

## 3. Answer

```text
main start
main before await
A start
B start
B end
A end
main done
```

## 4. Why

- `asyncio.create_task(...)` schedules a coroutine to run but does NOT start it immediately
  -- it only begins executing the next time the event loop gets a chance, which is at the
  next `await` that actually yields control. That's why both `"A start"` and `"B start"`
  print only after `main`'s synchronous code reaches `await task_a`, not at the
  `create_task` call sites.
- Both tasks are running concurrently once started. Task B's `asyncio.sleep(0.01)` is
  shorter than Task A's `asyncio.sleep(0.02)`, so B finishes first even though A was created
  first -- `await task_a` merely waits for A specifically; it doesn't block B from finishing
  in the meantime, and asyncio.gather-style scheduling here still lets B's completion print
  before A's.

## 5. 💡 Mental Model

```text
create_task() SCHEDULES a coroutine -- it doesn't run until the loop gets control
awaiting a slower task doesn't pause a faster sibling task that's already running
```
