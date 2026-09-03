"""Sync vs async HTTPX clients -- same API shape, different execution model.

These examples use httpx.MockTransport (httpx's own testing tool) instead
of hitting the real network, so they run offline and deterministically --
see https://www.python-httpx.org/advanced/transports/#mock-transports.
The client code itself is identical to what you'd write against a real API.

Requires: httpx (see requirements.txt)
Run: python3 sync_vs_async_client.py
"""
from __future__ import annotations
import asyncio
import httpx


def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"echo": request.url.path})


def sync_call() -> None:
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        response = client.get("https://api.example.com/status")
        print("sync:", response.json())


async def async_call() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        response = await client.get("https://api.example.com/status")
        print("async:", response.json())


if __name__ == "__main__":
    sync_call()  # blocks the thread until the response arrives
    asyncio.run(async_call())  # yields control back to the event loop while waiting
