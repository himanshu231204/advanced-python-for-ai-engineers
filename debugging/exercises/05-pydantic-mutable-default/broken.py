"""BROKEN: uses a plain Python mutable default (`tags: list[str] = []`)
directly as a Pydantic field default. Unlike a plain dataclass, Pydantic
v2 actually protects against the shared-object bug here -- but the field
has NO validation at all, so genuinely invalid data (an empty list of
required roles) sails through silently.

Run: python3 broken.py
"""
from __future__ import annotations
from pydantic import BaseModel


class AgentConfig(BaseModel):
    name: str
    allowed_roles: list[str] = []  # BUG: no constraint -- an empty list is accepted


if __name__ == "__main__":
    config = AgentConfig(name="support-bot", allowed_roles=[])
    print(config)  # accepted -- an agent with NO allowed roles can never act
