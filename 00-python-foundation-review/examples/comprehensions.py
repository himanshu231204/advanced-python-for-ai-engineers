"""Control flow and ranked retrieval filtering; run with Python 3.12+."""

from collections.abc import Iterator

type Hit = tuple[str, float]


def select_hits(hits: list[Hit], minimum: float) -> list[Hit]:
    """Keep qualifying hits in input order, including repeated document IDs."""
    return [hit for hit in hits if hit[1] >= minimum]


def score_band(score: float) -> str:
    if score >= 0.9:
        return "high"
    elif score >= 0.7:
        return "medium"
    else:
        return "low"


def route_action(action: str) -> str:
    match action:
        case "search":
            return "retrieve"
        case "answer":
            return "compose"
        case _:
            return "reject"


def main() -> None:
    numbers: list[int] = [1, 2, 3, 4]
    squares: list[int] = [number * number for number in numbers if number % 2 == 0]
    assert squares == [4, 16]
    assert [number for number in numbers if number > 10] == []
    assert {number % 2 for number in numbers} == {0, 1}

    prices: list[tuple[str, int]] = [("tea", 3), ("coffee", 5), ("tea", 4)]
    latest: dict[str, int] = {name: price for name, price in prices}
    assert latest == {"tea": 4, "coffee": 5}
    assert list(latest) == ["tea", "coffee"]

    hit_list: list[Hit] = [("b", 0.85), ("a", 0.4), ("b", 0.95), ("c", 0.7)]
    selected: list[Hit] = select_hits(hit_list, 0.7)
    assert selected == [("b", 0.85), ("b", 0.95), ("c", 0.7)]
    assert select_hits([], 0.7) == []
    assert select_hits(hit_list, 1.0) == []
    assert hit_list[1] == ("a", 0.4)

    stream: Iterator[str] = (doc_id for doc_id, score in hit_list if score >= 0.7)
    assert list(stream) == ["b", "b", "c"]
    assert list(stream) == []

    number: int = 99
    scoped: list[int] = [number for number in range(2)]
    assert scoped == [0, 1] and number == 99
    assert [score_band(score) for score in [0.9, 0.7, 0.1]] == ["high", "medium", "low"]
    assert [route_action(action) for action in ["search", "answer", "delete"]] == [
        "retrieve", "compose", "reject"
    ]

    batches: list[list[str]] = [["a", ""], ["b"]]
    flattened: list[str] = [item for batch in batches for item in batch if item]
    assert flattened == ["a", "b"]
    print(f"Selected hits: {selected}")
    print("Comprehension checks passed.")


if __name__ == "__main__":
    main()
