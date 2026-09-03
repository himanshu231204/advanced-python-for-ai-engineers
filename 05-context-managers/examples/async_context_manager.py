"""Async context managers: __aenter__ and __aexit__, used with `async with`.
This is exactly the shape of `async with httpx.AsyncClient() as client: ...`
(see 13-httpx-async-http).

Run: python3 async_context_manager.py
"""
from __future__ import annotations
import asyncio
from types import TracebackType


class AsyncLLMSession:
    """Simulates an async client session -- connecting is async (a real
    handshake/auth call), so __aenter__/__aexit__ must be async too."""

    def __init__(self, model: str) -> None:
        self.model = model

    async def __aenter__(self) -> "AsyncLLMSession":
        await asyncio.sleep(0.05)  # stand-in for an async connection handshake
        print(f"session opened for {self.model}")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        await asyncio.sleep(0.05)  # stand-in for an async connection teardown
        print(f"session closed for {self.model}")
        return False

    async def complete(self, prompt: str) -> str:
        await asyncio.sleep(0.05)
        return f"[{self.model}] response to: {prompt}"


async def main() -> None:
    async with AsyncLLMSession("gpt-mini") as session:
        result = await session.complete("hello")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
