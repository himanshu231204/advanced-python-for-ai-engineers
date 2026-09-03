"""AI Engineering Example -- parallelizing a CPU-heavy local embedding
computation across a batch of documents with multiprocessing. This is the
CPU-bound counterpart to 12-concurrency's asyncio fan-out: asyncio helps
when you're WAITING on an external API; multiprocessing helps when the
CPU itself is the bottleneck (e.g. running a model locally, not over HTTP).

Run: python3 parallel_batch_embedding.py
"""
from __future__ import annotations
import multiprocessing
import time


def cpu_heavy_embed(text: str) -> list[float]:
    """Pretend local embedding computation -- genuinely CPU-bound work,
    unlike an HTTP call to an embedding API (which would be I/O-bound and
    belong in 12-concurrency's asyncio.gather instead)."""
    return [float(sum(ord(c) for c in text) % (i + 1)) for i in range(200_000)]


def embed_batch_sequential(documents: list[str]) -> list[list[float]]:
    return [cpu_heavy_embed(doc) for doc in documents]


def embed_batch_parallel(documents: list[str], *, num_workers: int) -> list[list[float]]:
    with multiprocessing.Pool(processes=num_workers) as pool:
        return pool.map(cpu_heavy_embed, documents)


if __name__ == "__main__":
    documents = [f"document number {i}" for i in range(8)]

    start = time.perf_counter()
    embed_batch_sequential(documents)
    sequential_time = time.perf_counter() - start
    print(f"sequential: {sequential_time:.2f}s")

    start = time.perf_counter()
    embed_batch_parallel(documents, num_workers=4)
    parallel_time = time.perf_counter() - start
    print(f"parallel (4 workers): {parallel_time:.2f}s")
    print("meaningfully faster:", parallel_time < sequential_time * 0.7)  # True
