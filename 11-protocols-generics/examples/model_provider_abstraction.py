"""AI Engineering Example -- a model-provider abstraction built entirely
from structural typing: any object with a matching `generate` method works,
so swapping providers (or writing a fake for tests) never requires a shared
base class, registration, or inheritance.

Requires: Python 3.12+
Run: python3.12 model_provider_abstraction.py
"""
from __future__ import annotations
from typing import Protocol


class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class OpenAIStyleProvider:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate(self, prompt: str) -> str:
        return f"[{self.model}] {prompt[::-1]}"  # pretend completion


class LocalEchoProvider:
    def generate(self, prompt: str) -> str:
        return f"echo: {prompt}"


class FakeTestProvider:
    """Satisfies ModelProvider with zero setup -- ideal for unit tests."""

    def generate(self, prompt: str) -> str:
        return "fixed test response"


def run_pipeline(provider: ModelProvider, prompt: str) -> str:
    """This function has NO idea which concrete provider it received --
    and doesn't need to. Swapping providers means passing a different
    object in, nothing else changes."""
    return provider.generate(prompt)


if __name__ == "__main__":
    for provider in [OpenAIStyleProvider("gpt-mini"), LocalEchoProvider(), FakeTestProvider()]:
        print(run_pipeline(provider, "hello"))
