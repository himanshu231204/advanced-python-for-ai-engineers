"""RAG orchestration -- retrieve relevant chunks, augment a prompt with
them, then generate an answer. The three steps are kept as separate
functions with a typed boundary between them, so the retriever or the
generator can be swapped (a real vector DB, a real LLM API) without
touching the orchestration logic itself. Uses httpx.MockTransport so this
runs offline and deterministically, same as module 13's examples.

Run: python3 rag_orchestration.py
"""
from __future__ import annotations
import asyncio
import json
from dataclasses import dataclass

import httpx


@dataclass
class Chunk:
    text: str
    score: float


_DOCUMENTS = [
    Chunk("Contextvars isolate per-task state under asyncio.", score=0.0),
    Chunk("threading.local breaks under asyncio because tasks share a thread.", score=0.0),
    Chunk("Idempotency keys let a retried request replay its original result.", score=0.0),
]


def retrieve(query: str, top_k: int = 2) -> list[Chunk]:
    """Stands in for a real vector search -- a naive keyword overlap score
    is enough to demonstrate the pipeline shape."""
    query_words = set(query.lower().split())
    scored = [
        Chunk(doc.text, score=len(query_words & set(doc.text.lower().split())))
        for doc in _DOCUMENTS
    ]
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_k]


def augment_prompt(query: str, chunks: list[Chunk]) -> str:
    context = "\n".join(f"- {chunk.text}" for chunk in chunks)
    return f"Context:\n{context}\n\nQuestion: {query}\nAnswer using only the context above."


def _mock_llm(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    prompt = body["prompt"]
    answer = "yes, tasks are isolated" if "contextvars" in prompt.lower() else "not covered by context"
    return httpx.Response(200, json={"answer": answer})


async def generate(prompt: str, client: httpx.AsyncClient) -> str:
    response = await client.post("https://llm.example/generate", json={"prompt": prompt})
    return response.json()["answer"]


async def answer_question(query: str, client: httpx.AsyncClient) -> str:
    chunks = retrieve(query)
    prompt = augment_prompt(query, chunks)
    return await generate(prompt, client)


async def main() -> None:
    transport = httpx.MockTransport(_mock_llm)
    async with httpx.AsyncClient(transport=transport) as client:
        answer = await answer_question("does contextvars isolate task state?", client)
        print(answer)


if __name__ == "__main__":
    asyncio.run(main())
