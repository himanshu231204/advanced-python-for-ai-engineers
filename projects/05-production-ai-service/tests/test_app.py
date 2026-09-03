"""A pytest suite covering the core request path: health checks, a
cache miss followed by a cache hit, and the summarize response shape.

Run: pytest tests/
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_liveness() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_summarize_cache_miss_then_hit() -> None:
    text = "a unique piece of text for this test run"

    first = client.post("/summarize", json={"text": text})
    assert first.status_code == 200
    assert first.json()["cached"] is False

    second = client.post("/summarize", json={"text": text})
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert second.json()["summary"] == first.json()["summary"]


def test_summarize_rejects_missing_text() -> None:
    response = client.post("/summarize", json={})
    assert response.status_code == 422
