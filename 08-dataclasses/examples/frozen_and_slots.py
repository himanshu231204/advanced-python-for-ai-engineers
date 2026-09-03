"""`frozen=True` makes instances immutable (and hashable, if eq is also on --
the default); `slots=True` (3.10+) drops per-instance __dict__ for lower
memory use and faster attribute access.

Run: python3 frozen_and_slots.py
"""
from __future__ import annotations
from dataclasses import FrozenInstanceError, dataclass


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    tool_name: str
    result: str


if __name__ == "__main__":
    record = ToolCallRecord(tool_name="search_docs", result="3 results found")
    print(record)

    try:
        record.result = "tampered"  # type: ignore[misc]
    except FrozenInstanceError as e:
        print(f"caught: {e}")

    # slots=True means there's no per-instance __dict__ -- only the declared
    # fields exist, which is where the memory savings come from.
    print("has __dict__:", hasattr(record, "__dict__"))  # False

    # frozen instances are hashable by default -- usable as dict keys/set members.
    seen = {record}
    print(len(seen))
