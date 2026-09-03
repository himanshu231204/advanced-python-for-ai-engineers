"""Structured (JSON) logging: instead of a free-text message, emit one
JSON object per log line -- machine-parseable, so a log aggregator can
filter/query by field instead of grepping text.

Run: python3 structured_json_logging.py
"""
from __future__ import annotations
import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Anything passed via `extra={...}` shows up as an attribute on
        # the record -- pull out fields we specifically expect.
        for field in ("request_id", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload)


logger = logging.getLogger("structured_app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.propagate = False


if __name__ == "__main__":
    logger.info("request received", extra={"request_id": "req-123"})
    logger.info("request completed", extra={"request_id": "req-123", "duration_ms": 42})
