"""A quick preview of `Protocol` (structural typing): any object with the
right methods/attributes satisfies the type, with no inheritance required.
Full depth -- generic protocols, runtime-checkable protocols -- lives in
11-protocols-generics.

Run: python3 protocol_preview.py
"""
from __future__ import annotations
from typing import Protocol


class TextModel(Protocol):
    def generate(self, prompt: str) -> str: ...


class LocalEchoModel:
    """Never mentions TextModel anywhere -- it satisfies the protocol just
    by having a matching `generate` method (structural typing, aka
    "duck typing with a type checker watching")."""

    def generate(self, prompt: str) -> str:
        return f"echo: {prompt}"


def run_prompt(model: TextModel, prompt: str) -> str:
    return model.generate(prompt)


if __name__ == "__main__":
    print(run_prompt(LocalEchoModel(), "hello"))  # echo: hello
