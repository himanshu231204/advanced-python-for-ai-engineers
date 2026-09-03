"""Streaming pipeline -- chain small async generator STAGES together
(token source -> accumulator -> sentence splitter) instead of one
monolithic function. Each stage only knows how to transform what the
previous stage yields, so stages can be tested, reordered, or replaced
independently. Module 04 covered async generators; this is the
application pattern built on top of them.

Run: python3 streaming_pipeline.py
"""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator


async def token_source(tokens: list[str]) -> AsyncIterator[str]:
    """Stage 1 -- stands in for tokens arriving from an LLM API."""
    for token in tokens:
        await asyncio.sleep(0)  # pretend each token arrives over the network
        yield token


async def accumulate_text(tokens: AsyncIterator[str]) -> AsyncIterator[str]:
    """Stage 2 -- re-yields the running text built up so far, not just
    the newest token, which is what most streaming UIs actually render."""
    buffer = ""
    async for token in tokens:
        buffer += token
        yield buffer


async def split_into_sentences(running_text: AsyncIterator[str]) -> AsyncIterator[str]:
    """Stage 3 -- yields a NEW sentence exactly once, as soon as the
    running text contains a sentence-ending period it hasn't emitted yet."""
    emitted_up_to = 0
    async for text in running_text:
        if text.endswith(".") and len(text) > emitted_up_to:
            yield text[emitted_up_to:].strip()
            emitted_up_to = len(text)


async def main() -> None:
    tokens = ["Hello", " world", ".", " Contextvars", " isolate", " state", "."]

    pipeline = split_into_sentences(accumulate_text(token_source(tokens)))
    async for sentence in pipeline:
        print(f"sentence ready: {sentence!r}")


if __name__ == "__main__":
    asyncio.run(main())
