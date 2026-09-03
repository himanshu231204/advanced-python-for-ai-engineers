"""Mutability + aliasing bugs: passing a mutable object into a function
doesn't copy it -- the function receives a reference to the SAME object,
so mutating it there is visible to the caller too. This is the general
form of module 01's mutable default argument trap.

Run: python3 mutability_and_aliasing.py
"""
from __future__ import annotations


def add_step_wrong(history: list[str], step: str) -> list[str]:
    """Mutates the CALLER's list in place -- surprising if the caller
    didn't expect their list to change."""
    history.append(step)
    return history


def add_step_better(history: list[str], step: str) -> list[str]:
    """Returns a NEW list, leaving the caller's original untouched."""
    return [*history, step]


if __name__ == "__main__":
    original = ["search"]

    result = add_step_wrong(original, "summarize")
    print("caller's list was also mutated:", original)  # ['search', 'summarize'] -- surprising!
    print(result is original)  # True -- same object

    original2 = ["search"]
    result2 = add_step_better(original2, "summarize")
    print("caller's list is untouched:", original2)  # ['search']
    print("new list returned:", result2)  # ['search', 'summarize']
    print(result2 is original2)  # False -- a genuinely new object
