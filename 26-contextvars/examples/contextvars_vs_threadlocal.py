"""threading.local isolates state PER THREAD. asyncio runs all its tasks
on ONE thread, so threading.local can't tell concurrent tasks apart --
they'd all share the same value, which is exactly the bug contextvars
was introduced to fix.

Run: python3 contextvars_vs_threadlocal.py
"""
from __future__ import annotations
import asyncio
import contextvars
import threading

_thread_local = threading.local()
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


async def handle_with_threadlocal(request_id: str) -> str:
    _thread_local.request_id = request_id
    await asyncio.sleep(0.01)  # another task can run here, on the SAME thread
    return _thread_local.request_id  # may have been overwritten by that other task!


async def handle_with_contextvar(request_id: str) -> str:
    request_id_var.set(request_id)
    await asyncio.sleep(0.01)
    return request_id_var.get()  # correctly isolated per task


async def main() -> None:
    threadlocal_results = await asyncio.gather(
        handle_with_threadlocal("A"), handle_with_threadlocal("B"), handle_with_threadlocal("C")
    )
    print("threading.local results (BROKEN under asyncio):", threadlocal_results)
    # commonly ['C', 'C', 'C'] or similar -- all tasks see whichever value was
    # set LAST, because they all share the one thread's storage

    contextvar_results = await asyncio.gather(
        handle_with_contextvar("A"), handle_with_contextvar("B"), handle_with_contextvar("C")
    )
    print("contextvars results (correct):", contextvar_results)  # ['A', 'B', 'C']


if __name__ == "__main__":
    asyncio.run(main())
