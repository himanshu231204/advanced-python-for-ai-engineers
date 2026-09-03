"""A minimal graph runner -- chains async nodes together and STREAMS the
state after each node runs, with a retry + observability wrapper around
every node call. This is the underlying pattern a graph-based agent
framework like LangGraph builds a much richer API on top of.

Combines: type hints (07), dataclasses/Pydantic (08, 09),
async generators/streaming (04), Protocols (11),
the tool-calling pattern (28).

Run: python3 graph.py
"""
from __future__ import annotations
import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

from nodes import plan_node, respond_node, tool_node
from state import AgentState

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("langgraph_patterns")

Node = Callable[[AgentState], Awaitable[AgentState]]


async def run_node_with_retry(
    node: Node, state: AgentState, *, node_name: str, max_attempts: int = 2
) -> AgentState:
    """Observability + retry hooks around a single node's execution --
    the same idea as module 27's production patterns, applied per node."""
    for attempt in range(1, max_attempts + 1):
        start = asyncio.get_event_loop().time()
        try:
            new_state = await node(state)
            elapsed = asyncio.get_event_loop().time() - start
            logger.info("node=%s attempt=%d status=ok elapsed=%.3fs", node_name, attempt, elapsed)
            return new_state
        except Exception:
            logger.info("node=%s attempt=%d status=error", node_name, attempt)
            if attempt == max_attempts:
                raise
            await asyncio.sleep(0.01)
    raise RuntimeError("unreachable")


async def run_graph(query: str, nodes: list[tuple[str, Node]]) -> AsyncIterator[AgentState]:
    """Runs each node in sequence, YIELDING the state after every step --
    a caller can render intermediate progress instead of waiting for the
    whole graph to finish."""
    state = AgentState(query=query)
    for node_name, node in nodes:
        state = await run_node_with_retry(node, state, node_name=node_name)
        yield state


async def main() -> None:
    nodes: list[tuple[str, Node]] = [
        ("plan", plan_node),
        ("tool", tool_node),
        ("respond", respond_node),
    ]

    async for state in run_graph("what is contextvars used for?", nodes):
        print(f"--- after node, plan={state.plan!r} answer={state.final_answer!r}")

    print(f"\nfinal answer: {state.final_answer}")


if __name__ == "__main__":
    asyncio.run(main())
