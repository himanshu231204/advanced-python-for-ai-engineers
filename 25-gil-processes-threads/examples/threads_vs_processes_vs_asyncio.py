"""A single side-by-side measurement: for the SAME CPU-bound task,
threading gives almost no speedup (the GIL), multiprocessing gives a real
one (separate interpreters/cores). asyncio isn't measured here because it
doesn't even attempt to parallelize CPU-bound work in the first place --
see 03-asyncio for that.

Run: python3 threads_vs_processes_vs_asyncio.py
"""
from __future__ import annotations
import multiprocessing
import threading
import time


def cpu_bound(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def run_sequential(n: int, times: int) -> float:
    start = time.perf_counter()
    for _ in range(times):
        cpu_bound(n)
    return time.perf_counter() - start


def run_threaded(n: int, times: int) -> float:
    start = time.perf_counter()
    threads = [threading.Thread(target=cpu_bound, args=(n,)) for _ in range(times)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.perf_counter() - start


def run_multiprocess(n: int, times: int) -> float:
    start = time.perf_counter()
    with multiprocessing.Pool(processes=times) as pool:
        pool.map(cpu_bound, [n] * times)
    return time.perf_counter() - start


if __name__ == "__main__":
    n, times = 8_000_000, 2

    sequential = run_sequential(n, times)
    threaded = run_threaded(n, times)
    multiprocess = run_multiprocess(n, times)

    print(f"sequential:     {sequential:.2f}s (baseline)")
    print(f"threading:      {threaded:.2f}s (expect ~= sequential -- the GIL)")
    print(f"multiprocessing: {multiprocess:.2f}s (expect notably faster -- real parallelism)")
