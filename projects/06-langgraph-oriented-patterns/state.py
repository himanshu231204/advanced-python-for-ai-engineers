"""Typed state passed between graph nodes -- every node receives one of
these and returns a new one. Nothing here is LangGraph-specific; it's the
plain-Python shape a graph-based agent framework is built on top of.
"""
from __future__ import annotations
from pydantic import BaseModel


class ToolCall(BaseModel):
    tool: str
    args: str
    result: str | None = None


class AgentState(BaseModel):
    query: str
    plan: str | None = None
    tool_calls: list[ToolCall] = []
    final_answer: str | None = None
