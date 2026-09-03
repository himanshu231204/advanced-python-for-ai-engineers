from demo_pkg import summarize_lengths


def test_summarize_lengths() -> None:
    assert summarize_lengths(["a", "bb", "ccc"]) == {"a": 1, "bb": 2, "ccc": 3}
