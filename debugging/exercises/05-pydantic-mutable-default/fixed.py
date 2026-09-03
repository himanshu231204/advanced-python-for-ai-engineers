"""FIXED: use Field(min_length=1) to enforce the real business rule --
every agent must have at least one allowed role.

Run: python3 fixed.py
"""
from __future__ import annotations
from pydantic import BaseModel, Field, ValidationError


class AgentConfig(BaseModel):
    name: str
    allowed_roles: list[str] = Field(min_length=1)  # FIX: reject an empty list


if __name__ == "__main__":
    config = AgentConfig(name="support-bot", allowed_roles=["read_docs"])
    print(config)

    try:
        AgentConfig(name="broken-bot", allowed_roles=[])
    except ValidationError as exc:
        print(f"rejected: {exc.error_count()} error(s)")
