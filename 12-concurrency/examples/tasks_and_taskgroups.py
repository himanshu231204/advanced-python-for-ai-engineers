"""asyncio.create_task schedules a coroutine to run independently, starting
immediately rather than waiting for an `await`. TaskGroup (3.11+) manages a
set of tasks together with STRUCTURED concurrency: if one task raises, the
others are cancelled automatically and the error propagates cleanly.

Run: python3 tasks_and_taskgroups.py
"""
from __future__ import annotations
import asyncio


async def fake_call(name: str, delay: float, *, fail: bool = False) -> str:
    await asyncio.sleep(delay)
    if fail:
        raise RuntimeError(f"{name} failed")
    return name


async def with_create_task() -> None:
    task_a = asyncio.create_task(fake_call("a", 0.1))
    task_b = asyncio.create_task(fake_call("b", 0.1))
    # both tasks are ALREADY running here, before either is awaited
    print(await task_a, await task_b)


async def with_task_group_success() -> None:
    results: list[str] = []
    async with asyncio.TaskGroup() as tg:
        tg.create_task(fake_call("x", 0.1)).add_done_callback(
            lambda t: results.append(t.result())
        )
        tg.create_task(fake_call("y", 0.1)).add_done_callback(
            lambda t: results.append(t.result())
        )
    print("task group results:", sorted(results))


async def with_task_group_failure() -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fake_call("ok", 0.2))
            tg.create_task(fake_call("boom", 0.05, fail=True))
    except* RuntimeError as eg:
        print("task group raised:", [str(e) for e in eg.exceptions])


async def main() -> None:
    await with_create_task()
    await with_task_group_success()
    await with_task_group_failure()


if __name__ == "__main__":
    asyncio.run(main())
