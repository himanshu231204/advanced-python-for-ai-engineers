"""Tool-calling interface -- a typed registry mapping a tool NAME (what an
LLM emits) to a validated input model and a callable. This is the pattern
underneath every "function calling" / "tool use" API: the model never
calls Python directly, it emits a name + arguments that your code
validates and dispatches.

Run: python3 tool_calling_interface.py
"""
from __future__ import annotations
from typing import Any, Callable
from pydantic import BaseModel


class SearchDocsArgs(BaseModel):
    query: str
    top_k: int = 3


class SendEmailArgs(BaseModel):
    to: str
    subject: str


def search_docs(args: SearchDocsArgs) -> str:
    return f"found {args.top_k} result(s) for {args.query!r}"


def send_email(args: SendEmailArgs) -> str:
    return f"email sent to {args.to} with subject {args.subject!r}"


class ToolRegistry:
    """Maps a tool name to (its input schema, the function to call)."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[type[BaseModel], Callable[[Any], str]]] = {}

    def register(self, name: str, schema: type[BaseModel], fn: Callable[[Any], str]) -> None:
        self._tools[name] = (schema, fn)

    def dispatch(self, name: str, raw_args: dict[str, object]) -> str:
        """Simulates handling one tool call the model asked for: look up
        the tool, VALIDATE the model's raw arguments against its schema
        (never trust them blindly), then call the function."""
        if name not in self._tools:
            raise ValueError(f"unknown tool: {name!r}")
        schema, fn = self._tools[name]
        validated_args = schema.model_validate(raw_args)
        return fn(validated_args)


if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register("search_docs", SearchDocsArgs, search_docs)
    registry.register("send_email", SendEmailArgs, send_email)

    # What an LLM's tool-call response typically looks like: a name + a raw dict.
    print(registry.dispatch("search_docs", {"query": "contextvars", "top_k": 2}))
    print(registry.dispatch("send_email", {"to": "a@example.com", "subject": "hi"}))

    try:
        registry.dispatch("search_docs", {"query": "x", "top_k": "not-a-number"})
    except Exception as exc:
        print(f"rejected bad tool call: {type(exc).__name__}")
