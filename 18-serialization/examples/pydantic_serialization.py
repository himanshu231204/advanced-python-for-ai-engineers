"""Pydantic handles the exact pitfalls from serialization_pitfalls.py
automatically: datetimes and Enums serialize correctly out of the box,
with no custom `default=` function needed.

Requires: pydantic (see 09-pydantic/requirements.txt)
Run: python3 pydantic_serialization.py
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class Role(Enum):  # a PLAIN Enum -- no `str` mixin needed, unlike raw json.dumps
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    created_at: datetime


if __name__ == "__main__":
    message = Message(role=Role.USER, content="hello", created_at=datetime(2024, 1, 1, 12, 0))

    print(message.model_dump())  # Python dict -- role is still the Enum member
    print(message.model_dump_json())  # JSON string -- role and datetime both serialize cleanly

    # Round-trips cleanly back into a real Message instance.
    restored = Message.model_validate_json(message.model_dump_json())
    print(restored == message)  # True
