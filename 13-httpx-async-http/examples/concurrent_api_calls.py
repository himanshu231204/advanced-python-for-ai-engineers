"""Calling multiple different APIs concurrently through one shared
AsyncClient -- the exact shape of a fan-out to an LLM API, a vector DB, and
a search API at once (see 03-asyncio and 12-concurrency for the underlying
asyncio patterns).

Requires: httpx (see requirements.txt)
Run: python3 concurrent_api_calls.py
"""
from __future__ import annotations
import asyncio
import httpx

_RESPONSES = {
    "/llm": {"text": "a generated answer"},
    "/vector-search": {"matches": ["doc-1", "doc-2"]},
    "/keyword-search": {"matches": ["doc-3"]},
}


def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=_RESPONSES[request.url.path])


async def call(client: httpx.AsyncClient, path: str) -> tuple[str, dict]:
    response = await client.get(f"https://api.example.com{path}")
    return path, response.json()


async def main() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        results = await asyncio.gather(
            call(client, "/llm"),
            call(client, "/vector-search"),
            call(client, "/keyword-search"),
        )
    for path, body in results:
        print(f"{path} -> {body}")


if __name__ == "__main__":
    asyncio.run(main())
