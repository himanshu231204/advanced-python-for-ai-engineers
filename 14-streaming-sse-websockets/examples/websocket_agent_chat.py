"""AI Engineering Example -- a bidirectional agent chat session over
WebSocket. Unlike an SSE completion (one request -> one streamed reply),
a chat session needs the client to keep sending NEW messages on the same
open connection -- exactly what WebSockets are for and SSE cannot do.

Requires: fastapi, websockets (see requirements.txt)
Run: python3 websocket_agent_chat.py
"""
from __future__ import annotations
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

app = FastAPI()


async def fake_agent_reply(message: str) -> list[str]:
    """Pretend the agent streams a reply in a couple of chunks, then a
    final marker -- similar to how a real token stream would arrive."""
    return [f"thinking about: {message!r}", f"answer: {message.upper()}", "[done]"]


@app.websocket("/ws/chat")
async def chat(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        user_message = await websocket.receive_text()
        if user_message == "close":
            break
        for chunk in await fake_agent_reply(user_message):
            await websocket.send_text(chunk)
    await websocket.close()


if __name__ == "__main__":
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_text("hello agent")
        for _ in range(3):
            print(ws.receive_text())

        # the SAME connection handles a second turn -- no new request needed
        ws.send_text("second turn")
        for _ in range(3):
            print(ws.receive_text())

        ws.send_text("close")
