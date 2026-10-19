"""Run in this project's directory to isolate its flat-module imports."""
import asyncio
from collections.abc import Awaitable, Callable

import pytest
from pydantic import ValidationError

from nodes import plan_node, respond_node, tool_node
from state import AgentState, ToolCall

Node = Callable[[AgentState], Awaitable[AgentState]]


def test_valid_chain_returns_new_states_without_mutating_inputs() -> None:
    state = AgentState(query="contextvars")
    for node in (plan_node, tool_node, respond_node):
        before = state.model_dump()
        updated = asyncio.run(node(state))
        assert updated is not state
        assert state.model_dump() == before
        state = updated

    assert state.plan == "search for: contextvars"
    assert state.tool_calls == [
        ToolCall(tool="search", args="contextvars", result="3 result(s) for 'contextvars'")
    ]
    assert state.final_answer == (
        "Based on 3 result(s) for 'contextvars', here's my answer to 'contextvars'."
    )


@pytest.mark.parametrize("node", [plan_node, respond_node])
def test_node_rejects_corrupted_query(node: Node) -> None:
    state = AgentState.model_construct(
        query=123, tool_calls=[ToolCall(tool="search", args="contextvars", result="found")]
    )
    with pytest.raises(ValidationError, match="query"):
        asyncio.run(node(state))


def test_tool_node_revalidates_unchanged_fields() -> None:
    state = AgentState.model_construct(query="contextvars", final_answer=123)
    with pytest.raises(ValidationError, match="final_answer"):
        asyncio.run(tool_node(state))
