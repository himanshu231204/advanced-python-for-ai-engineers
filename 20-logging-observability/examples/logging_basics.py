"""The standard library `logging` module: named loggers, levels, and
handlers -- print() doesn't give you any of this (levels, filtering,
routing to multiple destinations).

Run: python3 logging_basics.py
"""
from __future__ import annotations
import logging

logger = logging.getLogger("ai_app")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
logger.addHandler(handler)
logger.propagate = False  # don't also send these to the root logger's handlers

if __name__ == "__main__":
    logger.debug("this won't print -- DEBUG is below the logger's INFO level")
    logger.info("agent started")
    logger.warning("retrying after a transient failure")
    logger.error("giving up after max retries")

    # Levels are just integers underneath -- this is why "INFO < WARNING" works.
    print(logging.INFO, logging.WARNING, logging.ERROR)  # 20 30 40
