"""Concurrent RAG Pipeline -- fans out to multiple retrieval sources at
once, tolerates any one branch timing out, merges and reranks the
combined results, and feeds the top chunks to an LLM.

Combines: concurrency/fan-out (12), HTTPX-style async I/O (13),
typed Protocol-shaped results (11), Pydantic (09).

Run: python3 pipeline.py
"""
from __future__ import annotations
import asyncio
from pydantic import BaseModel

from retrieval_sources import RetrievedChunk, keyword_search, metadata_filter, vector_search

PER_BRANCH_TIMEOUT = 0.05


class RagAnswer(BaseModel):
    query: str
    used_chunks: list[RetrievedChunk]
    answer: str


async def _run_branch_with_timeout(coro, *, branch_name: str) -> list[RetrievedChunk]:
    """A slow or failing retrieval branch shouldn't take down the whole
    pipeline -- return an empty result for it instead."""
    try:
        return await asyncio.wait_for(coro, timeout=PER_BRANCH_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"[warn] {branch_name} timed out -- continuing without it")
        return []


def merge_and_rerank(results: list[list[RetrievedChunk]], *, top_k: int = 3) -> list[RetrievedChunk]:
    """Flatten all branches, drop duplicate text (keeping the higher-scored
    copy), then keep the top_k by score -- a simplified reranker."""
    best_by_text: dict[str, RetrievedChunk] = {}
    for branch_results in results:
        for chunk in branch_results:
            existing = best_by_text.get(chunk.text)
            if existing is None or chunk.score > existing.score:
                best_by_text[chunk.text] = chunk
    return sorted(best_by_text.values(), key=lambda c: c.score, reverse=True)[:top_k]


async def generate(query: str, chunks: list[RetrievedChunk]) -> str:
    """Stands in for a real LLM call -- summarizes what it was given."""
    await asyncio.sleep(0.005)
    if not chunks:
        return "no relevant context found"
    return f"based on {len(chunks)} source(s): {chunks[0].text}"


async def answer_query(query: str, *, simulate_timeout: bool = False) -> RagAnswer:
    branch_results = await asyncio.gather(
        _run_branch_with_timeout(vector_search(query), branch_name="vector"),
        _run_branch_with_timeout(keyword_search(query), branch_name="keyword"),
        _run_branch_with_timeout(
            metadata_filter(query, simulate_timeout=simulate_timeout), branch_name="metadata"
        ),
    )
    top_chunks = merge_and_rerank(list(branch_results))
    answer = await generate(query, top_chunks)
    return RagAnswer(query=query, used_chunks=top_chunks, answer=answer)


async def main() -> None:
    result = await answer_query("how do contextvars isolate async state?")
    print(f"query: {result.query}")
    for chunk in result.used_chunks:
        print(f"  [{chunk.source} score={chunk.score}] {chunk.text}")
    print(f"answer: {result.answer}")

    print("\n--- with the metadata branch timing out ---")
    result = await answer_query("contextvars", simulate_timeout=True)
    for chunk in result.used_chunks:
        print(f"  [{chunk.source} score={chunk.score}] {chunk.text}")
    print(f"answer: {result.answer}")


if __name__ == "__main__":
    asyncio.run(main())
