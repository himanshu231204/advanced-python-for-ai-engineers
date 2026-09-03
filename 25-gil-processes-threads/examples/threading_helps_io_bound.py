"""Threads DO help I/O-bound (blocking) work -- the GIL is released while
a thread is blocked waiting on I/O (like time.sleep, or a real blocking
network call), letting other threads run during that wait.

Run: python3 threading_helps_io_bound.py
"""
from __future__ import annotations
import threading
import time


def blocking_io_call() -> None:
    time.sleep(0.2)  # simulates a blocking network/file call -- releases the GIL


if __name__ == "__main__":
    start = time.perf_counter()
    blocking_io_call()
    blocking_io_call()
    blocking_io_call()
    sequential_time = time.perf_counter() - start
    print(f"sequential (1 thread, 3 calls): {sequential_time:.2f}s")  # ~0.6s

    start = time.perf_counter()
    threads = [threading.Thread(target=blocking_io_call) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    threaded_time = time.perf_counter() - start
    print(f"three threads (same work): {threaded_time:.2f}s")  # ~0.2s -- genuinely overlapped
    print("threads helped:", threaded_time < sequential_time * 0.5)  # True
