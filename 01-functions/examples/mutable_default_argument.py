"""The mutable default argument trap -- one of Python's most common bugs,
and a real one in chat/agent code that accumulates conversation history.

Run: python3 mutable_default_argument.py
"""
from __future__ import annotations


# WRONG: the default list is created ONCE, at function *definition* time,
# and silently reused across every call that doesn't pass its own list.
def add_message_wrong(message: str, history: list[str] = []) -> list[str]:
    history.append(message)
    return history


# BETTER: use None as a sentinel and build a fresh list on every call.
def add_message_better(message: str, history: list[str] | None = None) -> list[str]:
    if history is None:
        history = []
    history.append(message)
    return history


if __name__ == "__main__":
    print(add_message_wrong("hello"))          # ['hello']
    print(add_message_wrong("are you there?")) # ['hello', 'are you there?']  <- leaked!

    print(add_message_better("hello"))          # ['hello']
    print(add_message_better("are you there?")) # ['are you there?']  <- correct, isolated
