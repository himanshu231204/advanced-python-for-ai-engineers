"""AI Engineering Example -- an async generator streaming LLM tokens.

This is the exact shape FastAPI (see `14-streaming-sse-websockets`) turns
into a Server-Sent Events response: the endpoint handler does
`async for chunk in stream_llm_tokens(...)` and writes each chunk to the
response as it arrives, instead of waiting for the whole completion.

Run: python3 llm_token_stream.py
"""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator

_FAKE_RESPONSE = "Async generators let you stream results as they're produced."


async def stream_llm_tokens(text: str) -> AsyncIterator[str]:
    for word in text.split(" "):
        await asyncio.sleep(0.05)  # stand-in for the network wait between tokens
        yield word + " "


async def render_as_it_streams(tokens: AsyncIterator[str]) -> str:
    full_text = ""
    async for token in tokens:
        print(token, end="", flush=True)
        full_text += token
    print()
    return full_text


async def main() -> None:
    result = await render_as_it_streams(stream_llm_tokens(_FAKE_RESPONSE))
    assert result.strip() == _FAKE_RESPONSE


if __name__ == "__main__":
    asyncio.run(main())
