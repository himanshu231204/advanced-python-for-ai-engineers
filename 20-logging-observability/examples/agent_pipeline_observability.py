"""AI Engineering Example -- combining structured logging, a correlation
ID, and tracing spans around a multi-step agent pipeline (retrieve ->
generate -> respond). This is what makes a production agent's run
debuggable: every log line can be traced back to one request and one step.

Run: python3 agent_pipeline_observability.py
"""
from __future__ import annotations
import asyncio
import contextvars
import json
import logging
import time
from contextlib import contextmanager
from collections.abc import Iterator

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "request_id": request_id_var.get(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "step"):
            payload["step"] = record.step
        if hasattr(record, "duration_ms"):
            payload["duration_ms"] = record.duration_ms
        return json.dumps(payload)


logger = logging.getLogger("agent_pipeline")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.propagate = False


@contextmanager
def traced_step(name: str) -> Iterator[None]:
    start = time.perf_counter()
    logger.info(f"{name} started", extra={"step": name})
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(f"{name} finished", extra={"step": name, "duration_ms": duration_ms})


async def retrieve(query: str) -> list[str]:
    with traced_step("retrieve"):
        await asyncio.sleep(0.01)
        return [f"doc about {query}"]


async def generate(docs: list[str]) -> str:
    with traced_step("generate"):
        await asyncio.sleep(0.02)
        return f"answer using {len(docs)} document(s)"


async def run_agent(request_id: str, query: str) -> str:
    request_id_var.set(request_id)
    with traced_step("agent_run"):
        docs = await retrieve(query)
        return await generate(docs)


if __name__ == "__main__":
    result = asyncio.run(run_agent("req-42", "async generators"))
    print("final answer:", result)
