"""Liveness vs readiness -- two different questions an orchestrator (e.g.
Kubernetes) asks a service. Liveness: "is the process stuck/deadlocked and
needs a restart?" Readiness: "can it currently handle traffic?" Conflating
them causes either unnecessary restarts or traffic sent to a broken pod.

Run: python3 health_checks.py
"""
from __future__ import annotations
from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.testclient import TestClient


@dataclass
class ServiceState:
    llm_client_ready: bool = False
    vector_db_ready: bool = False
    startup_errors: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.llm_client_ready and self.vector_db_ready and not self.startup_errors


state = ServiceState()
app = FastAPI()


@app.get("/health/live")
def liveness() -> dict[str, str]:
    """Answers ONLY "is the process running and responsive?" -- always
    returns ok if this handler can even execute. Never checks dependencies:
    a slow downstream API should not get this pod restarted."""
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> dict[str, object]:
    """Answers "should traffic be routed here right now?" -- checks
    dependencies that must be up for a request to actually succeed."""
    if not state.is_ready:
        return {"status": "not_ready", "errors": state.startup_errors}
    return {"status": "ready"}


if __name__ == "__main__":
    client = TestClient(app)
    print(client.get("/health/live").json())
    print(client.get("/health/ready").json())  # not_ready -- dependencies not initialized yet

    state.llm_client_ready = True
    state.vector_db_ready = True
    print(client.get("/health/ready").json())  # ready
