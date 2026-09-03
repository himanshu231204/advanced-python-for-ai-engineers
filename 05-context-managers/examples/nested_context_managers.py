"""Nested and multiple context managers -- entered left to right, exited
right to left (innermost first).

Run: python3 nested_context_managers.py
"""
from __future__ import annotations
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def step(name: str) -> Iterator[None]:
    print(f"enter {name}")
    try:
        yield
    finally:
        print(f"exit {name}")


if __name__ == "__main__":
    # Multiple managers in one `with` -- equivalent to nesting them.
    with step("outer"), step("inner"):
        print("doing work")

    print()

    # Explicit nesting reads the same way and behaves identically.
    with step("outer"):
        with step("inner"):
            print("doing work")
