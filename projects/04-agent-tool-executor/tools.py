"""Typed tools an agent can call -- each implements the `Tool` Protocol,
so the executor can run any of them without knowing their concrete type.
`FlakyApiTool` is deterministic (fails a fixed number of times before
succeeding) so retry behavior is reproducible without real randomness.
"""
from __future__ import annotations
from typing import Protocol


class TransientToolError(Exception):
    """A retryable tool failure (e.g. a temporary network blip)."""


class Tool(Protocol):
    name: str

    async def run(self, args: str) -> str: ...


class SearchDocsTool:
    name = "search_docs"

    async def run(self, args: str) -> str:
        return f"found 2 result(s) for {args!r}"


class FlakyApiTool:
    """Simulates a tool backed by a flaky external API -- fails on its
    first `fail_count` calls, then succeeds."""

    name = "flaky_api"

    def __init__(self, fail_count: int = 2) -> None:
        self._fail_count = fail_count
        self._call_count = 0

    async def run(self, args: str) -> str:
        self._call_count += 1
        if self._call_count <= self._fail_count:
            raise TransientToolError(f"flaky_api attempt {self._call_count}: temporarily unavailable")
        return f"flaky_api result for {args!r} (succeeded on attempt {self._call_count})"


class BrokenTool:
    """Simulates a tool with a permanent bug -- retrying never helps."""

    name = "broken_tool"

    async def run(self, args: str) -> str:
        raise ValueError(f"broken_tool cannot handle args: {args!r}")
