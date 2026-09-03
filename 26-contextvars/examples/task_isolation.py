"""Each asyncio Task gets its OWN COPY of the current context at the
moment it's created. Setting a ContextVar inside one task does NOT leak
into sibling tasks, and does NOT leak back into the parent that created
them -- this is what makes contextvars safe for per-request state.

Run: python3 task_isolation.py
"""
from __future__ import annotations
import asyncio
import contextvars

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


async def handle_request(request_id: str) -> str:
    request_id_var.set(request_id)
    await asyncio.sleep(0.01)
    return request_id_var.get()


async def main() -> None:
    print("before any task:", request_id_var.get())  # "-" -- default, untouched

    results = await asyncio.gather(
        handle_request("req-A"),
        handle_request("req-B"),
        handle_request("req-C"),
    )
    print("each task saw its own value:", results)  # ['req-A', 'req-B', 'req-C']

    # Setting it inside the tasks above never affected the CALLER's context.
    print("after the tasks:", request_id_var.get())  # still "-"


if __name__ == "__main__":
    asyncio.run(main())
