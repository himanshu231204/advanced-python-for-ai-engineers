"""AI Engineering Example -- request-scoped state (user ID, request ID)
that any nested function/dependency can read, without threading it
through every call as a parameter. This is the exact mechanism behind
middleware-set request context in FastAPI and similar frameworks, and the
same pattern module 20 used for correlated logging.

Run: python3 request_scoped_state.py
"""
from __future__ import annotations
import asyncio
import contextvars
from dataclasses import dataclass

user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="anonymous")


@dataclass
class ToolCallLog:
    tool: str
    user_id: str


def log_tool_call(tool: str) -> ToolCallLog:
    """A deeply nested helper -- has no idea it's running inside a
    specific request, yet correctly attributes the call to the right user."""
    return ToolCallLog(tool=tool, user_id=user_id_var.get())


async def run_tool(tool: str) -> ToolCallLog:
    await asyncio.sleep(0.005)  # pretend the tool call itself is async work
    return log_tool_call(tool)


async def handle_agent_request(user_id: str, tool: str) -> ToolCallLog:
    """The ONE place that sets the context, at the top of a request."""
    user_id_var.set(user_id)
    return await run_tool(tool)


async def main() -> None:
    logs = await asyncio.gather(
        handle_agent_request("user-1", "search_docs"),
        handle_agent_request("user-2", "summarize"),
    )
    for log in logs:
        print(log)  # each ToolCallLog has the CORRECT user_id, never mixed up


if __name__ == "__main__":
    asyncio.run(main())
