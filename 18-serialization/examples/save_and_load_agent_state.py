"""AI Engineering Example -- persisting and reloading agent conversation
state to/from a JSON file: pathlib for the file handling, Pydantic for
correct serialization of the datetime/Enum fields involved.

Requires: pydantic (see 09-pydantic/requirements.txt)
Run: python3 save_and_load_agent_state.py
"""
from __future__ import annotations
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    timestamp: datetime


class AgentState(BaseModel):
    session_id: str
    messages: list[Message]


def save_state(state: AgentState, path: Path) -> None:
    path.write_text(state.model_dump_json(indent=2))


def load_state(path: Path) -> AgentState:
    return AgentState.model_validate_json(path.read_text())


if __name__ == "__main__":
    state = AgentState(
        session_id="session-1",
        messages=[
            Message(role=Role.USER, content="hello", timestamp=datetime(2024, 1, 1, 12, 0)),
            Message(role=Role.ASSISTANT, content="hi there", timestamp=datetime(2024, 1, 1, 12, 1)),
        ],
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "session-1.json"
        save_state(state, path)
        print(path.read_text())

        restored = load_state(path)
        print(restored == state)  # True -- a full, lossless round trip
