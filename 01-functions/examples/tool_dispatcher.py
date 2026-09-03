"""AI Engineering Example -- a minimal tool-calling dispatcher.

Shows *args/**kwargs and first-class functions used together to route a
parsed LLM tool-call request ({"name": ..., "arguments": {...}}) to the
matching Python function. This is the pattern behind every "function calling"
/ "tool use" feature in LLM APIs.

Run: python3 tool_dispatcher.py
"""
from __future__ import annotations
from collections.abc import Callable

ToolFn = Callable[..., str]

TOOLS: dict[str, ToolFn] = {}


def register_tool(name: str) -> Callable[[ToolFn], ToolFn]:
    """Tiny registration decorator -- functions are first-class, so we can
    store them in a plain dict keyed by the name the LLM will ask for."""

    def decorator(fn: ToolFn) -> ToolFn:
        TOOLS[name] = fn
        return fn

    return decorator


@register_tool("get_weather")
def get_weather(city: str, unit: str = "celsius") -> str:
    return f"Weather in {city}: 22 degrees {unit}"


@register_tool("search_docs")
def search_docs(query: str, *, top_k: int = 3) -> str:
    return f"Top {top_k} results for {query!r}"


def dispatch_tool_call(name: str, **kwargs: object) -> str:
    """Route a tool call by name, forwarding its arguments as **kwargs."""
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOLS[name](**kwargs)


if __name__ == "__main__":
    # This is roughly what an LLM's tool-call response looks like once parsed.
    llm_tool_call = {
        "name": "search_docs",
        "arguments": {"query": "asyncio timeouts", "top_k": 2},
    }
    result = dispatch_tool_call(llm_tool_call["name"], **llm_tool_call["arguments"])
    print(result)  # Top 2 results for 'asyncio timeouts'

    print(dispatch_tool_call("get_weather", city="Bengaluru"))
    # Weather in Bengaluru: 22 degrees celsius
