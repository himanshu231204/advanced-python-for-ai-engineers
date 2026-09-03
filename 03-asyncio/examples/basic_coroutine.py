"""The absolute basics: `async def` creates a coroutine function; calling it
creates a coroutine OBJECT that does nothing until something awaits/runs it.

Run: python3 basic_coroutine.py
"""
from __future__ import annotations
import asyncio


async def greet(name: str) -> str:
    await asyncio.sleep(0.1)  # stand-in for any real I/O wait (API call, DB query, ...)
    return f"Hello, {name}!"


async def main() -> None:
    message = await greet("AI Engineer")
    print(message)


if __name__ == "__main__":
    # asyncio.run() creates an event loop, runs `main()` to completion, and
    # closes the loop. This is the standard entry point for a top-level
    # async program.
    coro = greet("nobody")
    print(type(coro))  # <class 'coroutine'> -- nothing has run yet!
    coro.close()  # avoid a "coroutine was never awaited" warning for this unused one

    asyncio.run(main())
