"""The async iterator protocol underneath `async for`: __aiter__ and
__anext__ -- the async counterpart of module 02's __iter__/__next__.

Run: python3 async_iterator_protocol.py
"""
from __future__ import annotations
import asyncio


class AsyncCountdown:
    def __init__(self, n: int) -> None:
        self.n = n

    def __aiter__(self) -> "AsyncCountdown":
        return self

    async def __anext__(self) -> int:
        if self.n <= 0:
            raise StopAsyncIteration
        await asyncio.sleep(0.05)
        self.n -= 1
        return self.n + 1


async def main() -> None:
    async for value in AsyncCountdown(3):
        print(value)


if __name__ == "__main__":
    asyncio.run(main())
