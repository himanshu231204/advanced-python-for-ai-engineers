"""AI Engineering Example -- combining a typed Protocol interface (module
11) with FastAPI's Depends system so the LLM provider behind an endpoint
can be swapped at the wiring level, with zero changes to the endpoint's
own code -- production uses the real provider, tests inject a fake.

Requires: fastapi, httpx (see requirements.txt)
Run: python3 swappable_llm_provider.py
"""
from __future__ import annotations
from typing import Protocol
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class OpenAIStyleProvider:
    def generate(self, prompt: str) -> str:
        raise RuntimeError("would call a real, billed LLM API")


def get_model_provider() -> ModelProvider:
    return OpenAIStyleProvider()  # the ONE place that decides the real implementation


@app.get("/generate")
def generate(prompt: str, provider: ModelProvider = Depends(get_model_provider)) -> dict[str, str]:
    """This endpoint depends on the ModelProvider INTERFACE only -- it has
    no idea whether it's talking to a real API or a test fake."""
    return {"result": provider.generate(prompt)}


class FakeModelProvider:
    def generate(self, prompt: str) -> str:
        return f"fixed test response for: {prompt}"


if __name__ == "__main__":
    app.dependency_overrides[get_model_provider] = lambda: FakeModelProvider()

    client = TestClient(app)
    response = client.get("/generate", params={"prompt": "hello"})
    print(response.json())

    app.dependency_overrides.clear()
