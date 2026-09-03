"""BROKEN: forgot to await an async call. Calling an async function
without awaiting it doesn't run its body to completion -- it just
creates a coroutine object and immediately moves on.

Run: python3 broken.py
"""
from __future__ import annotations
import asyncio


async def fetch_answer() -> int:
    await asyncio.sleep(0.01)
    return 42


async def main() -> None:
    result = fetch_answer()  # BUG: missing `await`
    print(f"result: {result}")
    print(f"type: {type(result)}")


if __name__ == "__main__":
    asyncio.run(main())
