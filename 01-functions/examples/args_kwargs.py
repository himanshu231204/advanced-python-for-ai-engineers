"""*args and **kwargs -- collecting variable positional/keyword arguments.

Run: python3 args_kwargs.py
"""
from __future__ import annotations


def call_tool(name: str, *args: object, **kwargs: object) -> str:
    """Mimic a generic tool-calling interface: name + arbitrary params."""
    arg_list = ", ".join(str(a) for a in args)
    kwarg_list = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    parts = [p for p in (arg_list, kwarg_list) if p]
    return f"{name}({', '.join(parts)})"


if __name__ == "__main__":
    print(call_tool("search", "python asyncio", top_k=5, rerank=True))
    # search(python asyncio, top_k=5, rerank=True)

    # Unpacking an existing dict straight into keyword arguments.
    params = {"top_k": 3, "rerank": False}
    print(call_tool("search", "rag pipelines", **params))
    # search(rag pipelines, top_k=3, rerank=False)
