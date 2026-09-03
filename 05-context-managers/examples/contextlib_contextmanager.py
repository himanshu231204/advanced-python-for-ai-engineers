"""Building a context manager the easy way with @contextlib.contextmanager
-- a generator function where everything before `yield` is __enter__ and
everything after (inside a `finally`) is __exit__.

Run: python3 contextlib_contextmanager.py
"""
from __future__ import annotations
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def open_resource(name: str) -> Iterator[str]:
    print(f"opening {name}")
    try:
        yield f"handle-to-{name}"
    finally:
        print(f"closing {name}")  # ALWAYS runs, even if the block raises


if __name__ == "__main__":
    with open_resource("connection.db") as handle:
        print("using", handle)

    try:
        with open_resource("connection2.db"):
            raise ValueError("boom")
    except ValueError as e:
        print(f"caught: {e}")
