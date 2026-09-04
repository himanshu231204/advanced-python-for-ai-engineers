"""When you CAN'T rewrite a blocking call: offload it with asyncio.to_thread.

`await asyncio.sleep()` only helps when *you* control the code and can swap in
an async version. In real AI systems you often depend on a **synchronous
third-party SDK** -- an older LLM client, a sync vector-DB driver, a
`psycopg2` database call, a PDF parser -- that makes a blocking network/CPU
call you cannot change.

Calling that SDK directly inside `async def` freezes the whole event loop
(see blocking_vs_nonblocking.py). The fix is `asyncio.to_thread(fn, *args)`:
it runs the blocking function in a background thread and gives you an
awaitable, so the event loop stays free to run other coroutines while the
thread waits on I/O.

Run: python3 offloading_with_to_thread.py
"""
from __future__ import annotations
import asyncio
import time


# -- A synchronous SDK we do NOT control (imagine: an LLM or DB client) ------
def sync_llm_generate(prompt: str) -> str:
    """Blocking call: simulates a synchronous network request to an LLM API.
    We can't add `async` to it -- it lives in a library we import."""
    time.sleep(1)  # network wait, blocking
    return f"response to: {prompt}"


# -- WRONG: calling the blocking SDK directly on the event loop --------------
async def wrong_worker(prompt: str) -> str:
    # Freezes the entire loop for ~1s -- every other coroutine stalls too.
    return sync_llm_generate(prompt)


# -- RIGHT: offload the blocking SDK call to a worker thread ------------------
async def offloaded_worker(prompt: str) -> str:
    # The loop is free to run other tasks while this thread waits on I/O.
    return await asyncio.to_thread(sync_llm_generate, prompt)


async def main() -> None:
    prompts = ["a", "b", "c"]

    start = time.perf_counter()
    await asyncio.gather(*(wrong_worker(p) for p in prompts))
    print(f"direct blocking calls: {time.perf_counter() - start:.2f}s "
          f"(expect ~3s -- ran SEQUENTIALLY, loop was frozen)")

    start = time.perf_counter()
    await asyncio.gather(*(offloaded_worker(p) for p in prompts))
    print(f"offloaded with to_thread: {time.perf_counter() - start:.2f}s "
          f"(expect ~1s -- ran CONCURRENTLY across threads)")


if __name__ == "__main__":
    asyncio.run(main())
