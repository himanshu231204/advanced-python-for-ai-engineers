"""A minimal WebSocket endpoint: unlike SSE (server -> client only), a
WebSocket is bidirectional -- the client can keep sending messages after
the connection opens, and the server can reply to each one individually.

Requires: fastapi, websockets (see requirements.txt)
Run: python3 websocket_echo.py
"""
from __future__ import annotations
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

app = FastAPI()


@app.websocket("/ws/echo")
async def echo(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        if message == "close":
            break
        await websocket.send_text(f"echo: {message}")
    await websocket.close()


if __name__ == "__main__":
    client = TestClient(app)
    with client.websocket_connect("/ws/echo") as ws:
        ws.send_text("hello")
        print(ws.receive_text())  # echo: hello

        ws.send_text("again")
        print(ws.receive_text())  # echo: again

        ws.send_text("close")
