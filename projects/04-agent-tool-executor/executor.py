"""Agent Tool Executor -- lets an agent select and run tools
asynchronously by name, retrying only transient tool failures, and
always reporting back a structured, typed result instead of letting a
tool's exception propagate straight to the agent.

Combines: Protocols (11), async execution (12),
retries (15), the tool-calling pattern (28).

Run: python3 executor.py
"""
from __future__ import annotations
import asyncio
from pydantic import BaseModel

from tools import BrokenTool, FlakyApiTool, SearchDocsTool, Tool, TransientToolError


class ToolExecutionResult(BaseModel):
    tool_name: str
    succeeded: bool
    output: str | None = None
    error: str | None = None
    attempts: int


class ToolExecutor:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools: dict[str, Tool] = {tool.name: tool for tool in tools}

    async def execute(self, tool_name: str, args: str, *, max_attempts: int = 3) -> ToolExecutionResult:
        if tool_name not in self._tools:
            return ToolExecutionResult(
                tool_name=tool_name, succeeded=False,
                error=f"no such tool: {tool_name!r}", attempts=0,
            )

        tool = self._tools[tool_name]
        last_error = ""
        for attempt in range(1, max_attempts + 1):
            try:
                output = await tool.run(args)
                return ToolExecutionResult(
                    tool_name=tool_name, succeeded=True, output=output, attempts=attempt,
                )
            except TransientToolError as exc:
                last_error = str(exc)
                await asyncio.sleep(0.01 * (2 ** (attempt - 1)))  # exponential backoff
            except Exception as exc:  # a non-transient tool bug -- don't retry it
                return ToolExecutionResult(
                    tool_name=tool_name, succeeded=False, error=str(exc), attempts=attempt,
                )

        return ToolExecutionResult(
            tool_name=tool_name, succeeded=False, error=last_error, attempts=max_attempts,
        )


async def run_agent_turn(executor: ToolExecutor, tool_calls: list[tuple[str, str]]) -> list[ToolExecutionResult]:
    """Stands in for an agent that decided to call several tools in one turn."""
    return [await executor.execute(name, args) for name, args in tool_calls]


async def main() -> None:
    executor = ToolExecutor([SearchDocsTool(), FlakyApiTool(fail_count=2), BrokenTool()])

    results = await run_agent_turn(
        executor,
        [
            ("search_docs", "contextvars"),
            ("flaky_api", "fetch weather"),
            ("broken_tool", "anything"),
            ("no_such_tool", "anything"),
        ],
    )

    for result in results:
        status = "OK" if result.succeeded else "FAILED"
        detail = result.output if result.succeeded else result.error
        print(f"[{status}] tool={result.tool_name} attempts={result.attempts}: {detail}")


if __name__ == "__main__":
    asyncio.run(main())
