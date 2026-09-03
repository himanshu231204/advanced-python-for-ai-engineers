"""A minimal tracing concept: a context manager ("span") that logs when a
named step starts/ends and how long it took, with nesting reflected in
indentation -- the same core idea behind real tracing tools (OpenTelemetry,
etc.), stripped down to just the mental model.

Run: python3 tracing_multi_step_pipeline.py
"""
from __future__ import annotations
import time
from contextlib import contextmanager
from collections.abc import Iterator

_depth = 0


@contextmanager
def span(name: str) -> Iterator[None]:
    global _depth
    indent = "  " * _depth
    print(f"{indent}-> {name}")
    _depth += 1
    start = time.perf_counter()
    try:
        yield
    finally:
        _depth -= 1
        elapsed = time.perf_counter() - start
        print(f"{indent}<- {name} ({elapsed * 1000:.1f}ms)")


def retrieve() -> list[str]:
    with span("retrieve"):
        time.sleep(0.02)
        return ["doc-1", "doc-2"]


def generate(docs: list[str]) -> str:
    with span("generate"):
        with span("build_prompt"):
            time.sleep(0.005)
        with span("call_llm"):
            time.sleep(0.03)
        return f"answer based on {len(docs)} docs"


if __name__ == "__main__":
    with span("agent_run"):
        docs = retrieve()
        answer = generate(docs)
    print("result:", answer)
