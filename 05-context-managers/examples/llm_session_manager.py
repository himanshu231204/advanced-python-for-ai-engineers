"""AI Engineering Example -- a connection-pool-style async context manager
that guarantees cleanup even when a request inside the block fails. This is
exactly the pattern behind `async with httpx.AsyncClient() as client: ...`
(see 13-httpx-async-http).

Run: python3 llm_session_manager.py
"""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator


class LLMClient:
    def __init__(self) -> None:
        self.closed = False

    async def complete(self, prompt: str) -> str:
        if "fail" in prompt:
            raise RuntimeError("simulated API failure")
        await asyncio.sleep(0.05)
        return f"response to: {prompt}"


@asynccontextmanager
async def llm_client() -> AsyncIterator[LLMClient]:
    print("opening connection pool")
    client = LLMClient()
    try:
        yield client
    finally:
        client.closed = True
        print("connection pool closed")  # runs even if a request raised


async def main() -> None:
    async with llm_client() as client:
        print(await client.complete("hello"))

    # Even when the request fails, the pool still gets closed.
    try:
        async with llm_client() as client:
            print(await client.complete("please fail"))
    except RuntimeError as e:
        print(f"caught: {e}")


if __name__ == "__main__":
    asyncio.run(main())
