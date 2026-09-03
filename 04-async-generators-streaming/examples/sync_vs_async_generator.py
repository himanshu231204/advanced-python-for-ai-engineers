"""A sync generator that "waits" with time.sleep blocks the whole event loop
when driven from async code; an async generator that waits with
asyncio.sleep lets other tasks (like a heartbeat) interleave between yields.

Run: python3 sync_vs_async_generator.py
"""
from __future__ import annotations
import asyncio
import time
from collections.abc import AsyncIterator, Iterator


def sync_token_stream(n: int) -> Iterator[str]:
    for i in range(n):
        time.sleep(0.2)  # blocks the entire event loop, not just this generator
        yield f"token-{i}"


async def async_token_stream(n: int) -> AsyncIterator[str]:
    for i in range(n):
        await asyncio.sleep(0.2)  # yields control back to the event loop
        yield f"token-{i}"


async def heartbeat() -> None:
    for _ in range(5):
        print("...heartbeat...")
        await asyncio.sleep(0.1)


async def run_sync_version() -> None:
    async def consume_sync() -> None:
        for token in sync_token_stream(3):
            print(token)

    await asyncio.gather(consume_sync(), heartbeat())


async def run_async_version() -> None:
    async def consume_async() -> None:
        async for token in async_token_stream(3):
            print(token)

    await asyncio.gather(consume_async(), heartbeat())


if __name__ == "__main__":
    print("=== sync generator (blocks the loop -- heartbeats can't interleave) ===")
    asyncio.run(run_sync_version())

    print("\n=== async generator (heartbeats interleave between tokens) ===")
    asyncio.run(run_async_version())
