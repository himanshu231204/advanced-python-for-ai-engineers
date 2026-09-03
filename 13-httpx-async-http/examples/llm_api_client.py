"""AI Engineering Example -- a small async LLM API client wrapping HTTPX
behind an async context manager (05-context-managers), so the connection
pool opens once and always closes, no matter how the caller's code exits.

Requires: httpx (see requirements.txt)
Run: python3 llm_api_client.py
"""
from __future__ import annotations
import httpx


def llm_handler(request: httpx.Request) -> httpx.Response:
    prompt = request.read().decode()
    return httpx.Response(200, json={"completion": f"response to: {prompt}"})


class LLMClient:
    def __init__(self, base_url: str, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, transport=transport, timeout=10.0)

    async def __aenter__(self) -> "LLMClient":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        await self._client.aclose()
        return False

    async def complete(self, prompt: str) -> str:
        response = await self._client.post("/v1/completions", content=prompt.encode())
        response.raise_for_status()
        return response.json()["completion"]


async def main() -> None:
    transport = httpx.MockTransport(llm_handler)
    async with LLMClient("https://api.example.com", transport=transport) as client:
        result = await client.complete("hello")
        print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
