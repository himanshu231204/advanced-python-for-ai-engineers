"""pytest-asyncio: `@pytest.mark.asyncio` lets a test function itself be
`async def`, so it can `await` the async code under test directly instead
of manually driving an event loop.

Run: python3 -m pytest test_async_pytest.py -v
"""
from __future__ import annotations
import asyncio
import pytest
import pytest_asyncio


async def fetch_value(n: int) -> int:
    await asyncio.sleep(0.01)
    return n * n


@pytest.mark.asyncio
async def test_fetch_value() -> None:
    result = await fetch_value(4)
    assert result == 16


@pytest.mark.asyncio
async def test_concurrent_fetches() -> None:
    results = await asyncio.gather(*(fetch_value(i) for i in range(3)))
    assert results == [0, 1, 4]


@pytest_asyncio.fixture
async def async_resource():
    """Async fixtures need @pytest_asyncio.fixture, not plain
    @pytest.fixture -- useful for setup that itself needs an `await`
    (e.g. an async client)."""
    await asyncio.sleep(0)  # pretend async setup
    yield {"ready": True}


@pytest.mark.asyncio
async def test_async_fixture(async_resource: dict[str, bool]) -> None:
    assert async_resource["ready"] is True
