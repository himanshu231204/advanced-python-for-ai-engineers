"""AI Engineering Example -- lazily streaming LLM tokens with a generator.

A generator produces (and holds in memory) only one token at a time, which is
exactly what lets a UI start rendering a response before the full completion
exists. This is the synchronous ancestor of the async version in
`04-async-generators-streaming`.

Run: python3 token_stream.py
"""
from __future__ import annotations
from collections.abc import Iterator

_FAKE_RESPONSE = "Generators are Python's built-in lazy iteration primitive."


def stream_tokens(text: str) -> Iterator[str]:
    """Simulate an LLM yielding tokens one at a time instead of returning
    the whole completion in one shot."""
    for word in text.split(" "):
        yield word + " "


def render_as_it_streams(tokens: Iterator[str]) -> str:
    """A consumer that could just as easily be a terminal or a websocket --
    it never needs the full response sitting in memory at once."""
    full_text = ""
    for token in tokens:
        print(token, end="", flush=True)
        full_text += token
    print()
    return full_text


if __name__ == "__main__":
    result = render_as_it_streams(stream_tokens(_FAKE_RESPONSE))
    assert result.strip() == _FAKE_RESPONSE
