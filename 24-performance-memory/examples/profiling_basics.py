"""AI Engineering Example -- profiling a data pipeline to find the actual
bottleneck instead of guessing. cProfile records how much time is spent in
every function call; pstats formats the results into a readable report.

Run: python3 profiling_basics.py
"""
from __future__ import annotations
import cProfile
import pstats
import io


def fake_embed(text: str) -> list[float]:
    """Pretend embedding computation -- deliberately does real (wasteful)
    work so the profiler has something meaningful to attribute time to."""
    return [float(sum(ord(c) for c in text)) for _ in range(2000)]


def preprocess(text: str) -> str:
    return text.strip().lower()


def embed_documents(documents: list[str]) -> list[list[float]]:
    return [fake_embed(preprocess(doc)) for doc in documents]


if __name__ == "__main__":
    documents = [f"  Document number {i} about advanced python  " for i in range(20)]

    profiler = cProfile.Profile()
    profiler.enable()
    embed_documents(documents)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(5)  # top 5 functions by cumulative time

    report = stream.getvalue()
    # Confirm the function we expect to dominate actually shows up in the report.
    assert "fake_embed" in report
    print(report)
