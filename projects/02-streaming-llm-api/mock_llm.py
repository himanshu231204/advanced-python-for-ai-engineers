"""A deterministic, offline stand-in for a real LLM token stream. Real
code would replace this with a provider's actual streaming API call.
"""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator


async def stream_tokens(prompt: str) -> AsyncIterator[str]:
    """Yields tokens one at a time, as a real streaming LLM response would."""
    response = f"Here is a response to: {prompt}"
    for word in response.split(" "):
        await asyncio.sleep(0.001)  # pretend each token arrives over the network
        yield word + " "
