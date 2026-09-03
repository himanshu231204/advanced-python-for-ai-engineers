"""Why asyncio does NOT speed up CPU-bound work.

`cpu_bound` never awaits anything, so it never yields control back to the
event loop -- once it starts running, it hogs the single thread until it
returns. Gathering two of them still runs them one after another, not
concurrently. See `25-gil-processes-threads` for the actual fix
(multiprocessing).

Run: python3 cpu_bound_no_speedup.py
"""
from __future__ import annotations
import asyncio
import time

N = 5_000_000


async def cpu_bound(n: int) -> int:
    total = 0
    for i in range(n):  # pure computation -- no `await` anywhere in this loop
        total += i * i
    return total


async def main() -> None:
    start = time.perf_counter()
    result = await cpu_bound(N)
    single_call_time = time.perf_counter() - start
    print(f"one cpu_bound call: {single_call_time:.2f}s (result={result})")

    start = time.perf_counter()
    await asyncio.gather(cpu_bound(N), cpu_bound(N))
    gathered_time = time.perf_counter() - start
    print(f"two gathered cpu_bound calls: {gathered_time:.2f}s")
    print(f"expected if truly concurrent: ~{single_call_time:.2f}s -- actual is ~2x, no speedup")


if __name__ == "__main__":
    asyncio.run(main())
