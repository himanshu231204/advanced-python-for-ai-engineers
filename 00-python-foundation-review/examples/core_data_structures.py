"""Core containers in ranked retrieval; Python 3.12+, no dependencies."""


def select_chunks(
    ranked: list[tuple[str, int]],
    text_by_chunk: dict[tuple[str, int], str],
) -> list[str]:
    seen: set[tuple[str, int]] = set()
    context: list[str] = []
    for chunk_key in ranked:
        if chunk_key in seen:
            continue
        seen.add(chunk_key)
        context.append(text_by_chunk[chunk_key])
    return context


def unique_document_ids(chunks: list[tuple[str, int]]) -> list[str]:
    return list(dict.fromkeys(doc_id for doc_id, _ in chunks))


def count_stock(skus: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sku in skus:
        counts[sku] = counts.get(sku, 0) + 1
    return counts


def main() -> None:
    ranked: list[tuple[str, int]] = [("a", 0), ("b", 0), ("a", 0), ("a", 1)]
    texts: dict[tuple[str, int], str] = {
        ("a", 0): "First",
        ("b", 0): "Other",
        ("a", 1): "Second",
    }
    context: list[str] = select_chunks(ranked, texts)
    documents: list[str] = unique_document_ids(ranked)
    assert context == ["First", "Other", "Second"]
    assert documents == ["a", "b"]
    assert select_chunks([], {}) == []
    assert select_chunks([("a", 0), ("a", 0)], texts) == ["First"]
    assert unique_document_ids([]) == []
    assert unique_document_ids([("a", 0), ("a", 1)]) == ["a"]
    assert unique_document_ids([("b", 0), ("a", 0), ("b", 0)]) == ["b", "a"]
    assert count_stock([]) == {}
    assert count_stock(["pen", "book", "pen"]) == {"pen": 2, "book": 1}

    try:
        select_chunks([("missing", 0)], texts)
    except KeyError as exc:
        assert exc.args == (("missing", 0),)
    else:
        raise AssertionError("Missing retrieval keys must remain visible")

    original: list[list[str]] = [["user"]]
    shallow: list[list[str]] = original.copy()
    shallow[0].append("assistant")
    assert original == [["user", "assistant"]]
    isolated: list[list[str]] = [row.copy() for row in original]
    isolated[0].append("tool")
    assert original == [["user", "assistant"]]

    print(f"Context: {context}")
    print(f"Documents: {documents}")
    print("Core data structure checks passed.")


if __name__ == "__main__":
    main()
