"""TypedDict shapes a plain dict's keys/value types without adding any
runtime validation (see 09-pydantic for that); Literal restricts a value to
a fixed set of options -- perfect for role fields, status codes, etc.

Run: python3 typed_dict_and_literal.py
"""
from __future__ import annotations
from typing import Literal, TypedDict

Role = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: Role
    content: str


def render_transcript(messages: list[ChatMessage]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


if __name__ == "__main__":
    transcript: list[ChatMessage] = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is a TypedDict?"},
        {"role": "assistant", "content": "A typed shape for a plain dict."},
    ]
    print(render_transcript(transcript))

    # TypedDict is a purely static-analysis construct -- this dict is
    # actually just a plain dict at runtime, so Python won't stop you from
    # building a malformed one; only a type checker (mypy/pyright) will flag it.
    bad: ChatMessage = {"role": "system", "content": "fine"}
    bad["role"] = "moderator"  # a type checker would reject this; Python won't
    print(bad)
