"""The GIL (Global Interpreter Lock) lets only ONE thread execute Python
bytecode at a time, even on a multi-core machine. For CPU-bound work,
adding threads does NOT make it faster -- they still take turns on one core.

Run: python3 gil_and_cpu_bound_threads.py
"""
from __future__ import annotations
import threading
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
    print(f"sequential (1 thread, 2 calls): {sequential_time:.2f}s")

    start = time.perf_counter()
    t1 = threading.Thread(target=cpu_bound, args=(n,))
    t2 = threading.Thread(target=cpu_bound, args=(n,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    threaded_time = time.perf_counter() - start
    print(f"two threads (same work): {threaded_time:.2f}s")
    print("threads made it faster:", threaded_time < sequential_time * 0.8)
    # Expect False (or barely True) -- the GIL means these two threads
    # mostly take turns on one core, not run truly in parallel.
