"""FIXED: await the coroutine so it actually runs to completion and
hands back its return value instead of a pending coroutine object.

Run: python3 fixed.py
"""
from __future__ import annotations
import asyncio


async def fetch_answer() -> int:
    await asyncio.sleep(0.01)
    return 42


async def main() -> None:
    result = await fetch_answer()  # FIX: await it
    print(f"result: {result}")
    print(f"type: {type(result)}")


if __name__ == "__main__":
    asyncio.run(main())
