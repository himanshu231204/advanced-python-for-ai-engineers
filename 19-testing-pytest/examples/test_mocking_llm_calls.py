"""Mocking HTTP/LLM calls in tests: never hit a real API in a test suite --
use httpx.MockTransport (see 13-httpx-async-http) to fake the HTTP layer,
or monkeypatch to replace a function entirely.

Run: python3 -m pytest test_mocking_llm_calls.py -v
"""
from __future__ import annotations
import httpx
import pytest


async def call_llm(client: httpx.AsyncClient, prompt: str) -> str:
    response = await client.post("/v1/completions", content=prompt.encode())
    response.raise_for_status()
    return response.json()["completion"]


@pytest.mark.asyncio
async def test_call_llm_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        prompt = request.read().decode()
        return httpx.Response(200, json={"completion": f"response to: {prompt}"})

    async with httpx.AsyncClient(
        base_url="https://api.example.com", transport=httpx.MockTransport(handler)
    ) as client:
        result = await call_llm(client, "hello")

    assert result == "response to: hello"


def real_llm_call(prompt: str) -> str:
    raise RuntimeError("would hit a real, unreliable, billable service")


def summarize(prompt: str) -> str:
    """The function under test -- calls whatever `real_llm_call` currently
    points to, without knowing (or needing to know) it's been mocked."""
    return real_llm_call(f"summarize: {prompt}")


def test_monkeypatch_replaces_a_function(monkeypatch: pytest.MonkeyPatch) -> None:
    """monkeypatch swaps out a function for the duration of ONE test,
    automatically restoring the original afterward -- no manual cleanup."""

    def fake_llm_call(prompt: str) -> str:
        return f"[mocked] {prompt}"

    monkeypatch.setattr("test_mocking_llm_calls.real_llm_call", fake_llm_call)

    assert summarize("hello") == "[mocked] summarize: hello"
