"""Testing generators: consume with a plain `for`/`list()` for sync
generators, `async for`/an async comprehension for async generators
(see 02-iterators-generators and 04-async-generators-streaming).

Run: python3 -m pytest test_generators.py -v
"""
from __future__ import annotations
from collections.abc import AsyncIterator, Iterator
import asyncio
import pytest


def countdown(n: int) -> Iterator[int]:
    while n > 0:
        yield n
        n -= 1


def test_generator_yields_expected_sequence() -> None:
    assert list(countdown(3)) == [3, 2, 1]


def test_generator_is_exhausted_after_one_pass() -> None:
    gen = countdown(2)
    assert list(gen) == [2, 1]
    assert list(gen) == []  # already exhausted -- this is expected, not a bug


async def stream_tokens(text: str) -> AsyncIterator[str]:
    for word in text.split(" "):
        await asyncio.sleep(0)
        yield word


@pytest.mark.asyncio
async def test_async_generator_yields_expected_tokens() -> None:
    tokens = [t async for t in stream_tokens("advanced python testing")]
    assert tokens == ["advanced", "python", "testing"]
