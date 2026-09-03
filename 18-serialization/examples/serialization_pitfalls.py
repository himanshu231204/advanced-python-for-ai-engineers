"""Common JSON serialization pitfalls: datetimes, Enums, and bytes don't
serialize by default -- each needs an explicit conversion or a custom
`default=` function.

Run: python3 serialization_pitfalls.py
"""
from __future__ import annotations
import json
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    """Inheriting from `str` makes Enum members ALSO plain strings, which
    is why this specific pattern serializes fine below -- a plain
    `class Role(Enum)` would NOT."""

    USER = "user"
    ASSISTANT = "assistant"


def json_default(value: object) -> str:
    """A `default=` function json.dumps calls for anything it doesn't
    already know how to serialize."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


if __name__ == "__main__":
    # Pitfall 1: datetime isn't JSON-serializable by default.
    try:
        json.dumps({"created_at": datetime(2024, 1, 1)})
    except TypeError as e:
        print(f"pitfall 1 caught: {e}")
    print("fixed:", json.dumps({"created_at": datetime(2024, 1, 1)}, default=json_default))

    # Pitfall 2: a plain Enum does NOT serialize, even though it "looks" like a string.
    class PlainRole(Enum):
        USER = "user"

    try:
        json.dumps({"role": PlainRole.USER})
    except TypeError as e:
        print(f"pitfall 2 caught: {e}")

    # ...but a `str, Enum` mixin DOES, because it genuinely IS a str at runtime.
    print("str-Enum works directly:", json.dumps({"role": Role.USER}))

    # Pitfall 3: bytes aren't JSON-serializable either.
    try:
        json.dumps({"payload": b"raw bytes"})
    except TypeError as e:
        print(f"pitfall 3 caught: {e}")
    print("fixed:", json.dumps({"payload": b"raw bytes"}, default=json_default))
