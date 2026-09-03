"""AI Engineering Example -- a typed tool-calling contract combining
TypedDict, Literal, Callable, and Annotated so an agent, a tool registry,
and a type checker all agree on the exact shape of a tool call and its
result.

Run: python3 typed_tool_interface.py
"""
from __future__ import annotations
from collections.abc import Callable
from typing import Annotated, Literal, TypedDict

ToolStatus = Literal["ok", "error"]


class ToolCall(TypedDict):
    name: str
    arguments: dict[str, object]


class ToolResult(TypedDict):
    status: ToolStatus
    output: str


# Annotated attaches extra metadata to a type without changing what the type
# actually is -- a type checker still sees `int`; the metadata is there for
# documentation, or for tools (like Pydantic, see 09) that read it at runtime.
TopK = Annotated[int, "must be between 1 and 20"]

ToolFn = Callable[..., ToolResult]


def search_docs(query: str, top_k: TopK = 3) -> ToolResult:
    return {"status": "ok", "output": f"top {top_k} results for {query!r}"}


TOOLS: dict[str, ToolFn] = {"search_docs": search_docs}


def dispatch(call: ToolCall) -> ToolResult:
    tool = TOOLS.get(call["name"])
    if tool is None:
        return {"status": "error", "output": f"unknown tool: {call['name']}"}
    return tool(**call["arguments"])


if __name__ == "__main__":
    call: ToolCall = {"name": "search_docs", "arguments": {"query": "type hints", "top_k": 2}}
    print(dispatch(call))

    bad_call: ToolCall = {"name": "does_not_exist", "arguments": {}}
    print(dispatch(bad_call))
