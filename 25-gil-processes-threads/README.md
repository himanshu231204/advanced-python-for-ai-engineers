# 25 — GIL, Processes & Threads

**Level:** 4 (Deep Python) | **Status:** ✅ Written

Knowing what the GIL actually restricts -- and when threads, processes, or asyncio is the
right tool -- prevents wasted effort trying to "async away" CPU-bound work. Module 03 (§9)
already warned that asyncio doesn't help CPU-bound code; this module explains *why*, and
gives you the tool that actually does: `multiprocessing`.

---

## 1. What is it?

The **GIL (Global Interpreter Lock)** is a lock in CPython that allows only one thread to
execute Python bytecode at any given moment, even on a multi-core machine. **Threads** share
memory and are cheap, but are bottlenecked by the GIL for CPU-bound work. **Processes** each
get their own interpreter and memory space, genuinely running in parallel across cores.

## 2. Why does it exist?

The GIL simplifies CPython's internal memory management (reference counting, module 24)
enormously by avoiding the need for fine-grained locking around every object. The tradeoff:
pure-Python CPU-bound code can't use multiple threads to go faster, no matter how many CPU
cores the machine has -- only one thread runs Python bytecode at a time.

## 3. 💡 Mental Model

```text
GIL: only ONE thread runs Python bytecode at a time
        │
        ▼
I/O-bound work (waiting on network/disk) -> the GIL is RELEASED during
the wait -> threads (and asyncio) genuinely help here
        │
        ▼
CPU-bound work (pure computation) -> the GIL is held the whole time ->
threads DON'T help; only separate PROCESSES (their own interpreter each)
achieve real parallelism
```

## 4. Syntax

```python
import threading

t = threading.Thread(target=some_function, args=(arg,))
t.start()
t.join()

import multiprocessing

with multiprocessing.Pool(processes=4) as pool:
    results = pool.map(some_function, list_of_args)  # runs across separate processes
```

## 5. Minimal Example

```python
import threading, time

def blocking_call():
    time.sleep(0.2)  # I/O-bound (a wait) -- releases the GIL

threads = [threading.Thread(target=blocking_call) for _ in range(3)]
for t in threads: t.start()
for t in threads: t.join()
# takes ~0.2s total, not ~0.6s -- threads genuinely overlapped
```

## 6. What happens internally?

```text
threading.Thread(target=cpu_bound, args=(n,)).start()  x2
        │
        ▼
both threads are real OS threads, but CPython's GIL only lets ONE of
them execute Python bytecode at a time
        │
        ▼
the interpreter periodically switches which thread holds the GIL, so
they interleave -- but neither ever runs Python code truly SIMULTANEOUSLY
with the other
        │
        ▼
total wall-clock time is roughly the SAME as running both sequentially
(plus some switching overhead) -- no speedup
        │
        ▼
multiprocessing.Pool, in contrast, forks separate OS PROCESSES, each with
its own interpreter and its own GIL -- they genuinely run in parallel
across CPU cores
```

## 7. Comparison: asyncio vs Threading vs Multiprocessing

| | asyncio | Threading | Multiprocessing |
|---|---|---|---|
| Best for | I/O-bound (network, disk) | I/O-bound, especially blocking libraries with no async API | CPU-bound work |
| Limited by the GIL? | n/a -- single thread | yes, for CPU-bound code | no -- separate interpreters |
| Memory | shared, single process | shared (same process) | separate, per process |
| Typical count | thousands of coroutines | tens to low hundreds of threads | roughly # of CPU cores |
| AI use case | fanning out concurrent API calls | wrapping a blocking SDK with no async client | parallelizing a locally-run model/CPU-heavy preprocessing |

## 8. 🎯 AI Engineering Use Case

Running a CPU-heavy local computation (a local embedding model, heavy preprocessing) across a
batch of documents is exactly where `multiprocessing` helps and `asyncio`/threading do not --
the bottleneck is CPU, not waiting.

### Example A — Tiny

```python
with multiprocessing.Pool(processes=2) as pool:
    pool.map(cpu_bound, [n, n])
```

### Example B — Practical

```python
def run_multiprocess(n, times):
    with multiprocessing.Pool(processes=times) as pool:
        return pool.map(cpu_bound, [n] * times)
```

### Example C — AI Engineering

```python
def embed_batch_parallel(documents: list[str], *, num_workers: int) -> list[list[float]]:
    with multiprocessing.Pool(processes=num_workers) as pool:
        return pool.map(cpu_heavy_embed, documents)
```

Full runnable version, with measured timings: [`examples/parallel_batch_embedding.py`](examples/parallel_batch_embedding.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
asyncio
✅ Use for I/O-bound operations
❌ Don't expect it to speed up CPU-heavy Python code
→ Use multiprocessing for suitable CPU-bound workloads

THREADING
✅ Use for I/O-bound work, especially blocking libraries with no async API
❌ Don't expect it to speed up CPU-bound Python code -- the GIL blocks that

MULTIPROCESSING
✅ Use for genuinely CPU-bound work needing real parallelism
❌ Avoid for I/O-bound work -- the overhead of separate processes (startup,
   inter-process communication) isn't worth it when threads/asyncio would do
```

## 10. 🚨 Common Mistakes

**Mistake 1 — using threads to speed up CPU-bound Python code**

```python
# WRONG -- two threads running the SAME CPU-bound work still take turns
# on one core because of the GIL; this is barely (if at all) faster than
# running them one after another.
t1 = threading.Thread(target=cpu_bound, args=(n,))
t2 = threading.Thread(target=cpu_bound, args=(n,))
```

```python
# BETTER -- multiprocessing genuinely parallelizes CPU-bound work
with multiprocessing.Pool(processes=2) as pool:
    pool.map(cpu_bound, [n, n])
```

Runnable proof, with measured timings for all three approaches:
[`examples/threads_vs_processes_vs_asyncio.py`](examples/threads_vs_processes_vs_asyncio.py)

**Mistake 2 — reaching for multiprocessing on I/O-bound work**

```python
# WRONG -- spinning up separate processes just to wait on network calls
# adds real overhead (process startup, serialization between processes)
# for no benefit; asyncio or threading already solve this more cheaply.
with multiprocessing.Pool(processes=10) as pool:
    pool.map(call_slow_api, urls)
```

```python
# BETTER -- asyncio (module 03) is the right tool for I/O-bound fan-out
results = await asyncio.gather(*(call_slow_api(url) for url in urls))
```

**Mistake 3 — assuming threading never helps just because of the GIL**

```python
# WRONG ASSUMPTION -- "the GIL means threads are useless" is only true
# for CPU-bound work. For I/O-bound blocking calls, threads genuinely
# overlap, because the GIL is released during the wait.
```

```python
# CORRECT -- threading DOES help I/O-bound work
threads = [threading.Thread(target=blocking_io_call) for _ in range(3)]
```

Runnable proof: [`examples/threading_helps_io_bound.py`](examples/threading_helps_io_bound.py)

## 11. ⚡ Quick Tricks

```python
# The standard way to parallelize CPU-bound work across cores
with multiprocessing.Pool(processes=N) as pool:
    results = pool.map(fn, items)
```

```python
# Threads for wrapping a blocking (non-async) library's I/O calls
t = threading.Thread(target=blocking_call)
t.start()
t.join()
```

```python
# Check available CPU cores before deciding a worker count
import multiprocessing
multiprocessing.cpu_count()
```

## 12. Performance Considerations

- `multiprocessing` has real overhead: starting a process is more expensive than starting a
  thread, and arguments/results must be pickled (serialized) to cross process boundaries --
  worth it for substantial CPU-bound work, not for trivial tasks.
- The right number of worker processes for CPU-bound work is usually close to
  `multiprocessing.cpu_count()` -- more than that just adds contention, since there aren't
  more physical cores to actually run them on.

## 13. 🎤 Interview Questions

**Q: Why doesn't asyncio automatically make CPU-bound Python faster?**
A: asyncio achieves concurrency by yielding control at `await` points while waiting on I/O.
A CPU-bound task has nothing to wait on -- it never yields -- so it runs to completion on the
single event-loop thread, exactly like ordinary blocking code. There's no parallelism to gain
from asyncio for CPU-bound work; that requires actual OS-level parallelism (separate
processes).

**Q: What does the GIL actually prevent?**
A: It prevents more than one thread from executing Python bytecode at the same time within
one process, even on a multi-core machine. It does NOT prevent threads from running
concurrently while blocked on I/O -- the GIL is released during blocking calls, which is why
threading still helps I/O-bound work.

**Q: Why does `multiprocessing` avoid the GIL problem that `threading` has?**
A: Each process spawned by `multiprocessing` has its own separate Python interpreter, its own
memory space, and therefore its own GIL. Since there's no shared interpreter state between
processes, multiple processes can genuinely execute Python bytecode simultaneously across
different CPU cores.

**Q: When would you choose threading over multiprocessing for I/O-bound work, given asyncio
also exists?**
A: When working with a library that only offers a blocking (non-async) API and provides no
async alternative -- threading lets you run that blocking call without freezing your whole
program, without the heavier overhead multiprocessing would add for a purely I/O-bound task.

## 14. 🛠 Mini Exercise

Write `parallel_sum_of_squares(numbers: list[int], *, num_workers: int) -> list[int]` that
uses `multiprocessing.Pool` to compute the sum of squares up to each number in `numbers`
(reusing a `sum_of_squares(n)` helper function), across `num_workers` worker processes.

<details>
<summary>Solution</summary>

```python
import multiprocessing


def sum_of_squares(n: int) -> int:
    return sum(i * i for i in range(n))


def parallel_sum_of_squares(numbers: list[int], *, num_workers: int) -> list[int]:
    with multiprocessing.Pool(processes=num_workers) as pool:
        return pool.map(sum_of_squares, numbers)


if __name__ == "__main__":
    print(parallel_sum_of_squares([10, 100, 1000], num_workers=2))
    # [285, 328350, 332833500]
```

</details>

## 15. Real-World Challenge

Extend [`examples/parallel_batch_embedding.py`](examples/parallel_batch_embedding.py) to
measure and print the speedup ratio (`sequential_time / parallel_time`) for several different
`num_workers` values (1, 2, 4, 8), and observe how the speedup stops improving (or even gets
worse) once `num_workers` exceeds the machine's actual CPU core count.

## 16. Cheat Sheet

```text
GIL, PROCESSES & THREADS
↓

threading.Thread(target=fn, args=(...)).start() / .join()   I/O-bound only
multiprocessing.Pool(processes=N).map(fn, items)              CPU-bound, real parallelism

asyncio      -> I/O-bound, thousands of coroutines, single thread
threading    -> I/O-bound, blocking libraries with no async API
multiprocessing -> CPU-bound, genuine multi-core parallelism

WHEN TO USE
-> multiprocessing for CPU-bound work; asyncio/threading for I/O-bound work

COMMON MISTAKE
-> using threads to try to speed up pure-Python CPU-bound code (the GIL blocks this)

AI USE CASE
-> multiprocessing.Pool to parallelize a locally-run embedding/preprocessing batch
```

---

⬅ Back to [main README](../README.md)
