"""FIXED: create a fresh generator for each pass (or materialize it into
a list/tuple up front if it needs to be iterated more than once).

Run: python3 fixed.py
"""
from __future__ import annotations
from collections.abc import Iterator


def token_stream() -> Iterator[str]:
    for token in ["Hello", " ", "world"]:
        yield token


def render(tokens: Iterator[str]) -> str:
    return "".join(tokens)


if __name__ == "__main__":
    first_render = render(token_stream())   # FIX: a fresh generator each time
    second_render = render(token_stream())
    print(f"first render: {first_render!r}")
    print(f"second render: {second_render!r}")  # same text both times
