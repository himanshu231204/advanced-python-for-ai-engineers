"""Intentional bug: a retrieval adapter returns a numeric score as text."""
import logging

logger = logging.getLogger(__name__)


def rank_record(record: dict[str, object]) -> str:
    logger.info("ranking retrieval record; score_type=%s", type(record["score"]).__name__)
    score = record["score"]
    if score >= 0.7:  # type: ignore[operator]
        return "keep"
    return "discard"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(rank_record({"score": "0.82"}))


if __name__ == "__main__":
    main()
