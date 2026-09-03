"""BROKEN: stores a generator and tries to iterate it twice, expecting
the same results both times. A generator is a single-use iterator -- once
exhausted, it stays exhausted.

Run: python3 broken.py
"""
from __future__ import annotations
from collections.abc import Iterator


def token_stream() -> Iterator[str]:
    for token in ["Hello", " ", "world"]:
        yield token


def render(tokens: Iterator[str]) -> str:
    return "".join(tokens)


if __name__ == "__main__":
    tokens = token_stream()
    first_render = render(tokens)
    second_render = render(tokens)  # BUG: `tokens` is already exhausted here
    print(f"first render: {first_render!r}")
    print(f"second render: {second_render!r}")  # empty -- not the same text again
