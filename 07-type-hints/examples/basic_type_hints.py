"""Basic type hints: variables, function signatures, and built-in generic
containers. Python does NOT enforce these at runtime -- they're checked by
a separate tool (mypy, pyright) and read by editors/IDEs.

Run: python3 basic_type_hints.py
"""
from __future__ import annotations


def summarize(text: str, max_words: int = 50) -> str:
    words = text.split()
    return " ".join(words[:max_words])


def word_counts(texts: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for text in texts:
        for word in text.split():
            counts[word] = counts.get(word, 0) + 1
    return counts


def find_user(user_id: int, users: dict[int, str]) -> str | None:
    """`X | None` (not `Optional[X]`) is the modern way to say "this can be
    None" -- Python 3.10+ syntax, no `typing.Optional` import needed."""
    return users.get(user_id)


if __name__ == "__main__":
    print(summarize("advanced python for ai engineers is a learning repo", max_words=4))
    print(word_counts(["a b a", "b c"]))
    print(find_user(1, {1: "alice"}))
    print(find_user(99, {1: "alice"}))
