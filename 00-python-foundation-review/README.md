# 00 — Python Foundation Review

**Level:** Foundation | **Status:** ✅ Written

A fast prerequisite refresher before the advanced modules. Read the core-container lesson
below, then the four focused topics; this is not a Python-from-scratch course.

## Foundation topics

- [Core data structures: list / tuple / set / dict](#core-data-structures--must-know) — lesson below.
- [Control flow and comprehensions](control-flow-comprehensions.md).
- [Functions, scope, and references](functions-scope.md); continue with [module 01](../01-functions/README.md).
- [Exception basics](exception-basics.md); continue with [context managers](../05-context-managers/README.md) and [advanced handling](../15-error-handling-retries/README.md).
- [Modules and imports](modules-imports.md); continue with [packaging and uv](../23-packaging-modern-python/README.md).
- [Iterators and generators](../02-iterators-generators/README.md) — the full follow-on lesson.

## Core Data Structures — MUST KNOW

### 1. What is it?

Python's core containers organize values: `list` is an editable sequence, `tuple` is a
fixed sequence, `set` stores unique hashable values, and `dict` maps hashable keys to values.
They become chat histories, chunk coordinates, seen document IDs, and tool registries.

### 2. Why does it exist?

Chat history needs order and repeated values. Deduplication needs uniqueness. Tool dispatch
needs lookup by name. Choosing a container expresses the guarantees each operation needs.

### 3. 💡 Mental Model

```text
ranked chunks (list)
        |
        v
seen keys (set) --> keep first occurrence --> context (list: ranking retained)
        |
        +-- key: (document ID, chunk index) tuple
        +-- text lookup: dict[key, text]
```

Names reference objects. Assignment shares a container; it does not copy it. A tuple
prevents replacing its elements, but a mutable element inside it can still change.

### 4. Syntax

```python
messages: list[str] = ["system", "user", "user"]
chunk_key: tuple[str, int] = ("doc-1", 2)
seen: set[str] = {"doc-1", "doc-2"}
texts: dict[str, str] = {"doc-1": "Async I/O overlaps network waits."}
messages.append("assistant")
seen.add("doc-3")
texts["doc-2"] = "Generators produce values lazily."
empty_set: set[str] = set()  # {} creates a dict.
singleton: tuple[str] = ("doc-1",)
```

Strings and integers are hashable; lists and dicts are not. A tuple is hashable only
if all its elements are hashable. Dict keys and set elements must be hashable.

### 5. Minimal Example

**Example A — Tiny**

```python
ids: list[str] = ["b", "a", "b"]
pair: tuple[str, int] = ("b", 0)
unique: set[str] = set(ids)
counts: dict[str, int] = {"b": 2, "a": 1}
assert ids[0] == pair[0] == "b"
assert unique == {"a", "b"}
assert counts["b"] == 2
```

### 6. Step-by-Step Execution

```python
ranked_ids: list[str] = ["b", "a", "b", "c"]
seen: set[str] = set()
ordered: list[str] = []
for doc_id in ranked_ids:
    if doc_id not in seen:
        seen.add(doc_id)
        ordered.append(doc_id)
assert ordered == ["b", "a", "c"]
```

```text
ID    already seen?    action              ordered
b     no               add to set + list   [b]
a     no               add to set + list   [b, a]
b     yes              skip                [b, a]
c     no               add to set + list   [b, a, c]
```

The set checks membership; the list retains retrieval ranking. Iterating the set itself
would not preserve that ranking as a guarantee.

### 7. Comparison

| Container | Purpose | Order / duplicates | Mutable? | Typical cost | AI use case |
|---|---|---|---|---|---|
| `list` | Sequence | Ordered; duplicates allowed | Yes | Index O(1); membership O(n) | Chat history, ranked chunks |
| `tuple` | Fixed sequence | Ordered; duplicates allowed | Elements cannot be replaced | Index O(1); membership O(n) | Chunk coordinates |
| `set` | Uniqueness | No ordering guarantee; unique | Yes | Membership average O(1) | Seen IDs, allowed tools |
| `dict` | Key-to-value mapping | Insertion ordered; unique keys | Yes | Key lookup average O(1) | Tool/document lookup |

| Related concept | Mental model | When to use |
|---|---|---|
| Iterable | Anything `iter(...)` accepts, including all four containers | A caller needs to loop |
| Iterator | A cursor consumed by `next(...)` | Progressive reading |
| Generator | An iterator from a generator function/expression | Lazy chunk/token processing |

Containers hold their values; generators produce values on demand. See
[module 02](../02-iterators-generators/README.md) for exhaustion and iterator protocols.

### 8. 🎯 AI Engineering Use Case

**Example B — Practical:** count inventory by SKU; repeated entries mean more stock.

```python
def count_stock(skus: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sku in skus:
        counts[sku] = counts.get(sku, 0) + 1
    return counts

assert count_stock(["pen", "book", "pen"]) == {"pen": 2, "book": 1}
```

**Example C — AI Engineering:** deduplicate retrieved chunks while preserving ranking.
Use a composite key: deduplicating only by document ID would drop different chunks
from the same document.

```python
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

assert select_chunks(
    [("a", 0), ("b", 0), ("a", 0), ("a", 1)],
    {("a", 0): "First", ("b", 0): "Other", ("a", 1): "Second"},
) == ["First", "Other", "Second"]
```

A missing key raises `KeyError`, exposing inconsistent retrieval data rather than
silently shrinking context. This example needs no network or model credentials.

### 9. When to Use / When NOT to Use

WHEN TO USE

✅ Good for:
- Lists for ordered, editable batches and histories.
- Tuples for small fixed positional records and hashable composite keys.
- Sets for uniqueness and repeated membership checks.
- Dicts for lookup by ID/name with key insertion order.

WHEN NOT TO USE

❌ Avoid when:
- Sets would lose meaningful ranking or duplicates.
- A list would eagerly materialize a huge token stream.
- Tuple positions obscure the meaning of a large record.
- A plain dict is being mistaken for validated external input.

BETTER ALTERNATIVE

Use generators for lazy processing, `collections.deque` for FIFO operations,
[dataclasses](../08-dataclasses/README.md) for named records, and
[Pydantic](../09-pydantic/README.md) for validation at external boundaries.

### 10. 🚨 Common Mistakes

**Wrong: a set preserves ranking. Better: ordered deduplication.**

```python
ranked: list[str] = ["b", "a", "b"]
unordered: list[str] = list(set(ranked))
ordered: list[str] = list(dict.fromkeys(ranked))
assert ordered == ["b", "a"]
```

Set iteration has no ranking guarantee; dicts retain key insertion order.

**Wrong: copying the outer list isolates nested state. Better: copy the mutable layer.**

```python
original: list[list[str]] = [["user"]]
shallow: list[list[str]] = original.copy()
shallow[0].append("assistant")
assert original == [["user", "assistant"]]

isolated: list[list[str]] = [row.copy() for row in original]
isolated[0].append("tool")
assert original == [["user", "assistant"]]
```

This fix fits lists of lists of strings. Deeper graphs need a deliberate copy policy;
see [module 24](../24-performance-memory/README.md).

**Wrong: tuples are deeply immutable. Better: use immutable elements too.**

```python
mutable_record: tuple[list[str], int] = (["search"], 1)
mutable_record[0].append("fetch")
immutable_record: tuple[tuple[str, ...], int] = (("search", "fetch"), 1)
assert immutable_record[0] == ("search", "fetch")
```

### 11. ⚡ Quick Tricks

```python
ids: list[str] = ["b", "a", "b"]
unique_in_order: list[str] = list(dict.fromkeys(ids))
allowed: set[str] = {"search", "fetch"}
requested: set[str] = {"search", "delete"}
permitted: set[str] = requested & allowed
positions: dict[str, int] = {value: index for index, value in enumerate(ids)}
assert unique_in_order == ["b", "a"]
assert permitted == {"search"}
assert positions["b"] == 2  # Duplicate keys keep the last assigned value.
```

### 12. Performance Considerations

- List append is amortized O(1); inserting/removing at the front is O(n).
- Dict/set lookup is average O(1), worst-case O(n); hashing itself has a cost.
- Building a set costs O(n) average time and extra memory. For one scan of a tiny list,
  creating a set may be unnecessary.
- A list slice/copy costs O(k) for k copied references and shares nested objects.
- Deduplication stores O(u) keys for u unique chunks, even with a generator as input.
- `sorted(seen)` creates a new sorted list in O(u log u); sets themselves are not sorted.

### 13. 🎤 Interview Questions

**Why use both a set and a list?** The set checks uniqueness efficiently; the list
preserves first-seen order and supports indexing.

**Can a tuple be a dict key?** Yes, if all its elements are hashable. A tuple containing
a list is not hashable.

**What happens when a dict key is assigned again?** Its value is replaced; its insertion
position stays. Deleting and reinserting puts it at the end.

**Does `b = a` copy a list?** No. Both names reference the same object.

### 14. 🛠 Mini Exercise

Implement `unique_document_ids(chunks: list[tuple[str, int]]) -> list[str]`.
Return document IDs in first-seen order, regardless of chunk index.

```text
[]                                -> []
[("a", 0), ("a", 1)]               -> ["a"]
[("b", 0), ("a", 0), ("b", 0)]     -> ["b", "a"]
```

Explain why this deduplicates at a different level than `select_chunks`. The runnable
script includes the solution and assertions.

### 15. Real-World / Runnable Code Example

From the repository root, using Python 3.12+ and no dependencies:

```bash
python 00-python-foundation-review/examples/core_data_structures.py
```

The [script](examples/core_data_structures.py) combines all four containers and checks
empty input, repeated chunks, multiple chunks per document, missing keys, and nested copies.

```text
Context: ['First', 'Other', 'Second']
Documents: ['a', 'b']
Core data structure checks passed.
```

### 16. Cheat Sheet

| Need | Choose | Gotcha |
|---|---|---|
| Ordered editable values | `list[T]` | Membership scans; assignment aliases |
| Fixed positional record | `tuple[str, int]` | Mutable elements stay mutable |
| Uniqueness / membership | `set[T]` | Hashable elements; no ranking guarantee |
| Lookup by key | `dict[K, V]` | Hashable keys; duplicate keys overwrite |
| Unique IDs in first-seen order | `list(dict.fromkeys(ids))` | IDs must be hashable |
| Lazy stream | Generator, [module 02](../02-iterators-generators/README.md) | One-shot consumption |

---

⬅ Back to [main README](../README.md)
