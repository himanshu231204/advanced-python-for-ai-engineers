"""Correlation IDs via contextvars: attach one request ID to EVERY log
line produced while handling that request, without threading a parameter
through every function call -- and it stays correct across concurrent
async requests (each gets its own context). Full depth on contextvars is
in 26-contextvars; this is the logging-specific use of it.

Run: python3 correlation_ids.py
"""
from __future__ import annotations
import asyncio
import contextvars
import logging

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


logger = logging.getLogger("correlated_app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(request_id)s] %(message)s"))
handler.addFilter(RequestIdFilter())
logger.addHandler(handler)
logger.propagate = False


async def handle_request(request_id: str) -> None:
    request_id_var.set(request_id)
    logger.info("handling request")
    await asyncio.sleep(0.01)
    logger.info("request done")


async def main() -> None:
    # Two "concurrent requests" -- each keeps its OWN request_id throughout,
    # even though both run on the same event loop at the same time.
    await asyncio.gather(handle_request("req-A"), handle_request("req-B"))


if __name__ == "__main__":
    asyncio.run(main())
