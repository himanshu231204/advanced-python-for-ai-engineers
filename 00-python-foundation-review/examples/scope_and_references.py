"""Run with Python 3.12+: scope, retained state, and request ownership."""

from collections.abc import Callable


def make_counter() -> Callable[[], int]:
    count: int = 0

    def next_count() -> int:
        nonlocal count
        count += 1
        return count

    return next_count


def record_turn(prompt: str, history: list[str] | None = None) -> list[str]:
    turns: list[str] = [] if history is None else list(history)
    turns.append(prompt)
    return turns


def mutate_then_rebind(items: list[str]) -> list[str]:
    items.append("tool result")
    items = ["replacement"]
    return items


attempts: int = 0


def broken_increment() -> int:
    attempts += 1
    return attempts


def main() -> None:
    request_a: list[str] = record_turn("Explain RAG")
    request_b: list[str] = record_turn("Explain tools")
    followup: list[str] = record_turn("Give an example", request_a)
    assert request_a == ["Explain RAG"]
    assert request_b == ["Explain tools"]
    assert request_a is not request_b
    assert followup == ["Explain RAG", "Give an example"]

    original: list[str] = ["prompt"]
    replacement: list[str] = mutate_then_rebind(original)
    assert original == ["prompt", "tool result"]
    assert replacement == ["replacement"]

    counter_a: Callable[[], int] = make_counter()
    counter_b: Callable[[], int] = make_counter()
    assert (counter_a(), counter_a(), counter_b()) == (1, 2, 1)
    assert counter_a() == 3

    try:
        broken_increment()
    except UnboundLocalError as error:
        assert isinstance(error, UnboundLocalError)
    else:
        raise AssertionError("Expected an unbound local read")
    assert attempts == 0
    print("scope and request-state checks passed")


if __name__ == "__main__":
    main()
