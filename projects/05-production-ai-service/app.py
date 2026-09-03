"""Production AI Service -- a small but production-shaped FastAPI
service: config-driven setup, cached responses, retry/timeout on the LLM
call, structured logging with a request correlation ID, and health
checks.

Combines: config (21), caching (16), retries (15),
logging/correlation IDs (20, using contextvars from 26),
production patterns (27), testing (19).

Run the server: uvicorn app:app --reload
Run the demo:   python3 app.py
"""
from __future__ import annotations
import contextvars
import json
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from cache import TTLCache
from config import settings
from llm_client import LLMTimeoutError, summarize

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("production_ai_service")
logger.addFilter(_RequestIdFilter())

app = FastAPI()
cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)


class SummarizeRequest(BaseModel):
    text: str


class SummarizeResponse(BaseModel):
    summary: str
    cached: bool


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id_var.set(str(uuid.uuid4())[:8])
    return await call_next(request)


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(payload: SummarizeRequest) -> SummarizeResponse:
    cached = cache.get(payload.text)
    if cached is not None:
        logger.info(json.dumps({"request_id": request_id_var.get(), "event": "cache_hit"}))
        return SummarizeResponse(summary=cached, cached=True)

    logger.info(json.dumps({"request_id": request_id_var.get(), "event": "cache_miss"}))
    try:
        result = await summarize(payload.text)
    except LLMTimeoutError as exc:
        logger.info(json.dumps({"request_id": request_id_var.get(), "event": "llm_timeout"}))
        raise exc

    cache.set(payload.text, result)
    return SummarizeResponse(summary=result, cached=False)


if __name__ == "__main__":
    client = TestClient(app)
    print(client.get("/health/live").json())
    print(client.get("/health/ready").json())

    first = client.post("/summarize", json={"text": "contextvars isolate per-task state"})
    print(first.json())

    second = client.post("/summarize", json={"text": "contextvars isolate per-task state"})
    print(second.json())  # cached=True -- no second LLM call
