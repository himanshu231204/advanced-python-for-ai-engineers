"""multiprocessing sidesteps the GIL entirely by using separate OS
processes, each with its OWN Python interpreter and memory space -- this
is what actually achieves parallelism for CPU-bound work.

Run: python3 multiprocessing_basics.py
"""
from __future__ import annotations
import multiprocessing
import time


def cpu_bound(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


if __name__ == "__main__":
    n = 10_000_000

    start = time.perf_counter()
    cpu_bound(n)
    cpu_bound(n)
    sequential_time = time.perf_counter() - start
    print(f"sequential (1 process, 2 calls): {sequential_time:.2f}s")

    start = time.perf_counter()
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(cpu_bound, [n, n])
    multiprocess_time = time.perf_counter() - start
    print(f"two processes (same work): {multiprocess_time:.2f}s")
    print("processes made it faster:", multiprocess_time < sequential_time * 0.8)  # True
