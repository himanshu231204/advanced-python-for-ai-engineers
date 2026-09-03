"""Async generator functions: `async def` + `yield` together. Consumed with
`async for` instead of a plain `for`.

Run: python3 async_generator_basics.py
"""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator


async def countdown(n: int) -> AsyncIterator[int]:
    while n > 0:
        await asyncio.sleep(0.05)  # stand-in for any real async wait between values
        yield n
        n -= 1


async def main() -> None:
    async for value in countdown(3):
        print(value)


if __name__ == "__main__":
    asyncio.run(main())
