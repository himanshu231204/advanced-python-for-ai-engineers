"""Common mistake: forgetting `await`. Calling a coroutine function without
`await` just creates a coroutine object -- it never actually runs.

Run: python3 forgot_await.py
"""
from __future__ import annotations
import asyncio


async def fetch_llm_response(prompt: str) -> str:
    await asyncio.sleep(0.1)
    return f"response to: {prompt}"


async def wrong() -> None:
    # WRONG -- missing `await`. `result` is a coroutine object, not a string,
    # and the coroutine body never executes (Python even warns:
    # "coroutine 'fetch_llm_response' was never awaited").
    result = fetch_llm_response("hello")
    print("wrong:", result)
    result.close()  # suppress the warning for this deliberately-broken demo


async def correct() -> None:
    # BETTER -- `await` runs the coroutine and gives you its actual return value.
    result = await fetch_llm_response("hello")
    print("correct:", result)


if __name__ == "__main__":
    asyncio.run(wrong())
    asyncio.run(correct())
