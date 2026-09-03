"""Reusing one AsyncClient across many requests lets HTTPX pool and reuse
underlying connections (keep-alive), instead of paying a fresh TCP/TLS
handshake for every single request. MockTransport can't show the network
cost directly, but it proves the CODE pattern -- one client instance,
many requests -- which is what actually matters for real APIs.

Requires: httpx (see requirements.txt)
Run: python3 client_reuse_and_pooling.py
"""
from __future__ import annotations
import asyncio
import httpx

call_count = 0


def handler(request: httpx.Request) -> httpx.Response:
    global call_count
    call_count += 1
    return httpx.Response(200, json={"path": request.url.path})


async def with_shared_client(paths: list[str]) -> None:
    """ONE client, reused for every request -- the recommended pattern."""
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        responses = await asyncio.gather(*(client.get(f"https://api.example.com{p}") for p in paths))
        print("shared client results:", [r.json() for r in responses])


async def with_new_client_per_call(paths: list[str]) -> None:
    """WRONG in production -- a new client (and in real usage, a new
    connection pool) is created and torn down for every single call."""
    results = []
    for p in paths:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            response = await client.get(f"https://api.example.com{p}")
            results.append(response.json())
    print("new-client-per-call results:", results)


async def main() -> None:
    paths = ["/a", "/b", "/c"]
    await with_shared_client(paths)
    await with_new_client_per_call(paths)


if __name__ == "__main__":
    asyncio.run(main())
