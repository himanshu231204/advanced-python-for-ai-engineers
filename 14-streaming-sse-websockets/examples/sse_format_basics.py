"""The raw Server-Sent Events wire format -- no framework needed to
understand it. Each event is plain text: a `data:` line (or several),
followed by a BLANK line to mark the event's end. This is exactly what a
browser's EventSource (or any SSE client) parses.

Run: python3 sse_format_basics.py
"""
from __future__ import annotations
from collections.abc import Iterator


def format_sse_event(data: str, *, event: str | None = None) -> str:
    lines = []
    if event is not None:
        lines.append(f"event: {event}")
    lines.append(f"data: {data}")
    return "\n".join(lines) + "\n\n"  # the blank line is what terminates an event


def parse_sse_stream(raw: str) -> Iterator[str]:
    """A minimal client-side parser: split on the blank-line event
    terminator and pull out each event's data payload."""
    for chunk in raw.split("\n\n"):
        if not chunk.strip():
            continue
        for line in chunk.splitlines():
            if line.startswith("data: "):
                yield line.removeprefix("data: ")


if __name__ == "__main__":
    stream = (
        format_sse_event("Hello") + format_sse_event("World") + format_sse_event("done", event="end")
    )
    print(repr(stream))

    for data in parse_sse_stream(stream):
        print("event data:", data)
