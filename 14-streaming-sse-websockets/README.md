# 14 — Streaming: SSE & WebSockets

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

Streaming LLM output to a frontend needs a transport: Server-Sent Events for one-way token
streams, WebSockets for bidirectional agent/chat sessions. Module 04 built the async
generator that *produces* the stream; this module is what actually gets it over HTTP to a
client.

> Examples in this module need `fastapi`, `httpx`, and `websockets`. See
> [`requirements.txt`](requirements.txt). They use FastAPI's `TestClient` to drive requests
> in-process, so they run with no real server or open port needed.

---

## 1. What is it?

**SSE (Server-Sent Events)** is a simple, one-way (server → client) streaming protocol built
on plain HTTP: the server keeps a response open and sends `data: ...` chunks over time.
**WebSockets** are a separate, full-duplex protocol: after an initial handshake, both sides
can send messages to each other at any time over one long-lived connection.

## 2. Why does it exist?

```text
LLM
 ↓
tokens/events
 ↓
async generator
 ↓
FastAPI
 ↓
SSE
 ↓
Frontend
```

An LLM produces its response incrementally. Without a streaming transport, the frontend has
to wait for the entire completion before showing anything. SSE (for one-shot completions) and
WebSockets (for ongoing chat/agent sessions) are the two standard ways to get those
incrementally-produced tokens to the browser as they're generated.

## 3. 💡 Mental Model

```text
SSE         -> a one-way megaphone: server talks, client only listens (over one HTTP response)
WebSocket   -> a phone call: either side can talk at any time, on one open connection
```

## 4. Syntax

```python
# SSE -- an async generator formatted as SSE events, streamed via FastAPI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def event_stream():
    for token in tokens:
        yield f"data: {token}\n\n"   # the blank line ends each event

@app.get("/stream")
async def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")

# WebSocket -- bidirectional, one connection, many messages either way
from fastapi import WebSocket

@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        await websocket.send_text(f"reply to {message}")
```

## 5. Minimal Example

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def numbers():
    for i in range(3):
        yield f"data: {i}\n\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(numbers(), media_type="text/event-stream")
```

## 6. What happens internally?

```text
StreamingResponse(event_stream(), media_type="text/event-stream")
        │
        ▼
FastAPI/Starlette sends response HEADERS immediately (status 200,
Content-Type: text/event-stream), WITHOUT waiting for the body
        │
        ▼
it then iterates the async generator, writing each yielded chunk to the
open HTTP connection as soon as it's produced
        │
        ▼
the client (browser EventSource, or any SSE-aware HTTP client) reads and
parses each `data: ...\n\n` block as it arrives, firing an event per block
```

## 7. Comparison: SSE vs WebSocket

| | SSE | WebSocket |
|---|---|---|
| Direction | server -> client only | bidirectional |
| Transport | plain HTTP | its own protocol (upgraded from HTTP) |
| Reconnection | automatic, built into the browser's `EventSource` | you implement it yourself |
| Complexity | simple -- it's just a long HTTP response | more moving parts (handshake, framing) |
| Best for | one-shot completions, notifications, progress updates | multi-turn chat, agent sessions, anything needing client -> server messages mid-stream |
| AI use case | streaming a single LLM completion to the UI | an ongoing agent chat session with multiple turns |

## 8. 🎯 AI Engineering Use Case

Streaming a single LLM completion is a perfect SSE use case -- the server produces tokens,
the client only listens. A multi-turn agent chat needs WebSockets, since the client keeps
sending new messages on the same connection as the conversation continues.

### Example A — Tiny

```python
async def event_stream():
    for i in range(3):
        yield f"data: {i}\n\n"
```

### Example B — Practical

```python
@app.websocket("/ws/echo")
async def echo(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        await websocket.send_text(f"echo: {message}")
```

### Example C — AI Engineering

```python
async def stream_llm_tokens(text: str):
    for word in text.split(" "):
        yield f"data: {word}\n\n"

@app.get("/completion")
async def completion():
    return StreamingResponse(stream_llm_tokens(response_text), media_type="text/event-stream")
```

Full runnable version: [`examples/llm_token_sse_stream.py`](examples/llm_token_sse_stream.py)
-- and the bidirectional chat counterpart:
[`examples/websocket_agent_chat.py`](examples/websocket_agent_chat.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
SSE
✅ Use for: one-way streaming (a single LLM completion, progress updates, notifications)
❌ Avoid when: the client needs to send messages mid-stream (use WebSocket instead)

WEBSOCKETS
✅ Use for: multi-turn agent/chat sessions, anything genuinely bidirectional
❌ Avoid when: it's just one-way streaming -- SSE is simpler, works over plain
   HTTP (proxies/load balancers understand it natively), and reconnects itself

BETTER ALTERNATIVE
Default to SSE for streaming a single response. Reach for WebSockets only
when the client genuinely needs to send new messages while the connection
is still open.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — malformed SSE events (missing the blank-line terminator)**

```python
# WRONG -- no blank line between events; a real SSE client can't tell
# where one event ends and the next begins.
yield f"data: {token}\n"
```

```python
# BETTER -- the double newline (one blank line) is what marks an event's end
yield f"data: {token}\n\n"
```

Runnable proof of the correct raw format: [`examples/sse_format_basics.py`](examples/sse_format_basics.py)

**Mistake 2 — using SSE for something that actually needs bidirectional messages**

```python
# WRONG -- trying to force a multi-turn chat through SSE means opening a
# NEW request for every single user message, losing any shared session state
# an open connection would have given you for free.
@app.get("/chat")
async def chat(message: str):
    return StreamingResponse(stream_reply(message), media_type="text/event-stream")
# every new user message = a whole new HTTP request
```

```python
# BETTER -- one WebSocket connection handles the whole conversation
@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        for chunk in await get_reply(message):
            await websocket.send_text(chunk)
```

**Mistake 3 — forgetting to set the correct media type on an SSE response**

```python
# WRONG -- without the right media type, some clients/proxies won't treat
# this as an event stream (e.g. might buffer the whole response first).
return StreamingResponse(event_stream())
```

```python
# BETTER
return StreamingResponse(event_stream(), media_type="text/event-stream")
```

## 11. ⚡ Quick Tricks

```python
# SSE endpoint in one line of setup
return StreamingResponse(event_stream(), media_type="text/event-stream")
```

```python
# Format an SSE event with an explicit event type (not just default "message")
yield f"event: token\ndata: {chunk}\n\n"
```

```python
# Drive a streaming endpoint in tests without a real server
from fastapi.testclient import TestClient
with TestClient(app).stream("GET", "/stream") as response:
    for line in response.iter_lines():
        ...
```

```python
# Test a WebSocket endpoint the same way -- no real socket needed
with TestClient(app).websocket_connect("/ws/chat") as ws:
    ws.send_text("hi")
    print(ws.receive_text())
```

## 12. Performance Considerations

- SSE responses stay open for the duration of the stream -- make sure your server/reverse
  proxy timeouts are configured for long-lived connections, not just typical request/response
  latencies.
- WebSockets hold a connection open per client for the whole session; at scale, that's a
  meaningfully different resource profile (one persistent connection per active user) than
  short-lived HTTP requests, and worth factoring into capacity planning.

## 13. 🎤 Interview Questions

**Q: How would you stream an LLM response to a frontend?**
A: Wrap the async generator producing tokens (module 04) in a FastAPI `StreamingResponse`
with `media_type="text/event-stream"`, formatting each token as an SSE `data: ...\n\n` chunk.
The browser's `EventSource` (or any SSE client) then receives and renders each token as it
arrives, instead of waiting for the full response.

**Q: SSE vs WebSocket -- how do you decide?**
A: If the server only ever needs to push data to the client (a single completion, progress
updates, notifications), SSE is simpler: it's plain HTTP, works through most
proxies/load balancers without special handling, and reconnects automatically. If the client
also needs to send new messages while the connection is open (an ongoing chat/agent session),
that requires a WebSocket's bidirectional channel.

**Q: What does the blank line in an SSE event actually do?**
A: It's the event delimiter -- everything before it (one or more `data:`/`event:`/`id:`
lines) is one event; the blank line tells the client "this event is complete, start parsing
the next one." Omitting it means a client can't reliably tell where one event ends and the
next begins.

**Q: Why can't a single HTTP request/response handle a multi-turn agent chat the way a
WebSocket can?**
A: An HTTP request/response is inherently one-shot: the client sends one request, the server
sends one response (even if that response is streamed), and the connection is done. A new
user message would require an entirely new HTTP request, losing the ability to keep sending
new client messages on the same already-open connection the way a WebSocket allows.

## 14. 🛠 Mini Exercise

Write an async generator `sse_events(items: list[str])` that yields each item as a properly
formatted SSE event (`data: {item}\n\n`), followed by one final `event: done\ndata: \n\n`
event marking the end of the stream. Then write a small parser that reads the raw
concatenated output and returns `(items, is_done)`.

<details>
<summary>Solution</summary>

```python
from collections.abc import AsyncIterator
import asyncio


async def sse_events(items: list[str]) -> AsyncIterator[str]:
    for item in items:
        yield f"data: {item}\n\n"
    yield "event: done\ndata: \n\n"


def parse_stream(raw: str) -> tuple[list[str], bool]:
    items = []
    is_done = False
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        if block.startswith("event: done"):
            is_done = True
        elif block.startswith("data: "):
            items.append(block.removeprefix("data: "))
    return items, is_done


async def main() -> None:
    raw = "".join([chunk async for chunk in sse_events(["a", "b", "c"])])
    print(parse_stream(raw))  # (['a', 'b', 'c'], True)


asyncio.run(main())
```

</details>

## 15. Real-World Challenge

Extend [`examples/websocket_agent_chat.py`](examples/websocket_agent_chat.py) so the server
can also proactively push a message to the client without waiting for a new user message
first (e.g. a "typing..." indicator sent immediately after `receive_text()`, before the full
reply is ready) -- practice using the bidirectional channel in both directions within a single
turn, not just strict request/reply.

## 16. Cheat Sheet

```text
SSE & WEBSOCKETS
↓

StreamingResponse(gen(), media_type="text/event-stream")   SSE endpoint
yield f"data: {chunk}\n\n"                                  one SSE event

@app.websocket("/ws/path")                                  WebSocket endpoint
await websocket.accept()
await websocket.receive_text() / .send_text(...)            bidirectional messages

WHEN TO USE
-> SSE for one-way streaming; WebSocket for bidirectional/multi-turn sessions

COMMON MISTAKE
-> missing the blank-line event terminator in an SSE `data:` chunk

AI USE CASE
-> SSE for a single streamed LLM completion; WebSocket for a multi-turn agent chat
```

---

⬅ Back to [main README](../README.md)
