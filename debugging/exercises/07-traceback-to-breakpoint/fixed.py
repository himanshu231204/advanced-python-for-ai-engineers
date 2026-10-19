"""Normalize and validate a retrieval score at the adapter boundary."""
import logging
import math

logger = logging.getLogger(__name__)


def rank_record(record: dict[str, object]) -> str:
    raw_score = record.get("score")
    logger.info("ranking retrieval record; score_type=%s", type(raw_score).__name__)
    if isinstance(raw_score, bool) or not isinstance(raw_score, (str, int, float)):
        raise ValueError("score must be a number between 0 and 1")
    try:
        score = float(raw_score)
    except ValueError as exc:
        raise ValueError("score must be numeric") from exc
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("score must be finite and between 0 and 1")
    return "keep" if score >= 0.7 else "discard"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(rank_record({"score": "0.82"}))


if __name__ == "__main__":
    main()
