"""field() with default_factory -- the dataclass-native fix for module 01's
mutable default argument trap. A plain `history: list[str] = []` in a
dataclass body is actually a SyntaxError/ValueError precisely to stop you
from making that mistake.

Run: python3 field_defaults.py
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ConversationState:
    user_id: str
    history: list[str] = field(default_factory=list)  # fresh list per instance
    turn_count: int = 0


if __name__ == "__main__":
    a = ConversationState(user_id="u1")
    b = ConversationState(user_id="u2")

    a.history.append("hello")

    print(a.history)  # ['hello']
    print(b.history)  # []  <- NOT shared with `a`, unlike a mutable default arg would be
