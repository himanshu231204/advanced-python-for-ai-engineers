"""Async node functions -- each takes an AgentState and returns a new
AgentState. Nodes are plain async functions with a typed input/output
boundary; a real graph framework just adds edges and scheduling on top
of exactly this shape.
"""
from __future__ import annotations
import asyncio
from typing import Protocol

from state import AgentState, ToolCall


class Tool(Protocol):
    async def run(self, args: str) -> str: ...


class SearchTool:
    async def run(self, args: str) -> str:
        await asyncio.sleep(0.005)
        return f"3 result(s) for {args!r}"


TOOL_REGISTRY: dict[str, Tool] = {"search": SearchTool()}


async def plan_node(state: AgentState) -> AgentState:
    """Decides what to do -- here, always "search for the query"."""
    return state.model_copy(update={"plan": f"search for: {state.query}"})


async def tool_node(state: AgentState) -> AgentState:
    """Dispatches to a tool via the typed registry -- the same
    tool-calling pattern as 28-ai-engineering-patterns."""
    tool = TOOL_REGISTRY["search"]
    result = await tool.run(state.query)
    call = ToolCall(tool="search", args=state.query, result=result)
    return state.model_copy(update={"tool_calls": [*state.tool_calls, call]})


async def respond_node(state: AgentState) -> AgentState:
    """Produces the final answer from whatever the tool node found."""
    last_call = state.tool_calls[-1]
    answer = f"Based on {last_call.result}, here's my answer to {state.query!r}."
    return state.model_copy(update={"final_answer": answer})
