"""Three independent, deterministic retrieval sources -- stand-ins for a
real vector search, keyword search, and metadata filter. Each returns a
typed result so the pipeline can merge and rerank across sources without
caring which one produced what.
"""
from __future__ import annotations
import asyncio
from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    source: str
    text: str
    score: float


_KNOWLEDGE_BASE = [
    "Contextvars isolate per-task state under asyncio.",
    "threading.local breaks under asyncio because tasks share one thread.",
    "Idempotency keys let a retried request replay its original result.",
    "Health checks split liveness (is it alive) from readiness (can it serve traffic).",
]


async def vector_search(query: str) -> list[RetrievedChunk]:
    await asyncio.sleep(0.01)
    words = set(query.lower().split())
    return [
        RetrievedChunk(source="vector", text=text, score=0.9)
        for text in _KNOWLEDGE_BASE
        if words & set(text.lower().split())
    ][:2]


async def keyword_search(query: str) -> list[RetrievedChunk]:
    await asyncio.sleep(0.01)
    return [
        RetrievedChunk(source="keyword", text=text, score=0.6)
        for text in _KNOWLEDGE_BASE
        if any(word in text.lower() for word in query.lower().split())
    ][:2]


async def metadata_filter(query: str, *, simulate_timeout: bool = False) -> list[RetrievedChunk]:
    """The metadata source is deliberately slow when `simulate_timeout` is
    set -- demonstrates the pipeline surviving one branch timing out."""
    await asyncio.sleep(1.0 if simulate_timeout else 0.01)
    return [RetrievedChunk(source="metadata", text=_KNOWLEDGE_BASE[0], score=0.4)]
