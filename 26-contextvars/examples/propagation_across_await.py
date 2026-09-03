"""A ContextVar set before an `await` is still visible to code AFTER that
await, and inside any function called from there -- it propagates through
the normal call chain of one coroutine, without being passed as an
explicit parameter anywhere.

Run: python3 propagation_across_await.py
"""
from __future__ import annotations
import asyncio
import contextvars

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


async def deeply_nested_function() -> None:
    """Never received request_id as a parameter -- reads it from context."""
    print("deeply nested sees:", request_id_var.get())


async def middle_function() -> None:
    await asyncio.sleep(0.01)  # crossing an await boundary changes nothing
    await deeply_nested_function()


async def handle_request(request_id: str) -> None:
    request_id_var.set(request_id)
    await middle_function()


if __name__ == "__main__":
    asyncio.run(handle_request("req-abc"))
    # deeply nested sees: req-abc
