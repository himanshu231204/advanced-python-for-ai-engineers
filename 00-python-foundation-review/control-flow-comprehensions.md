# Control Flow and Comprehensions — MUST KNOW

**Status:** ✅ Written | Python 3.12+ | No dependencies

## 1. What is it?

Control flow chooses which statements run and how often. A comprehension builds a
container by iterating, optionally filtering, and transforming values. In an AI backend,
these choices determine which retrieved hits reach a prompt and in what order.

## 2. Why does it exist?

Simple transformations should be easy to inspect. Comprehensions express the result;
loops expose intermediate state, branching, logging, and early exits. Choose the form
that makes the retrieval or validation policy obvious to the next engineer.

## 3. 💡 Mental Model

```text
input order --> for each item --> predicate? -- no --> skip
                                    |
                                   yes
                                    v
                              transform --> output
```

A trailing `if` filters items. An expression such as `"keep" if valid else "drop"`
chooses a value for every item; it does not remove items.

## 4. Syntax

The loop refresher below uses `continue` to skip an item and `break` to stop scanning.
`if/elif/else` checks conditions in order; only the first true branch runs.

```python
scores: list[float] = [-1.0, 0.5, 0.95, 0.8]
bands: list[str] = []
for score in scores:
    if score < 0:
        continue
    if score >= 0.9:
        bands.append("high")
        break
    elif score >= 0.7:
        bands.append("medium")
    else:
        bands.append("low")
assert bands == ["low", "high"]

remaining: int = 2
while remaining > 0:
    remaining -= 1
assert remaining == 0

action: str = "search"
match action:
    case "search":
        route: str = "retrieve"
    case "answer":
        route = "compose"
    case _:
        route = "reject"
assert route == "retrieve"
```

`match` compares patterns, with the first matching case selected. Quoted strings above
are literal patterns; a bare name generally captures a value, rather than comparing it.
Use `if` for numeric thresholds and `match` for recognizable shapes or literal alternatives.

```python
from collections.abc import Iterator

values: list[int] = [1, 2, 2, 3]
kept: list[int] = [value * 10 for value in values if value >= 2]
unique: set[int] = {value for value in values}
lookup: dict[int, int] = {value: value * 10 for value in values}
lazy: Iterator[int] = (value * 10 for value in values if value >= 2)
labels: list[str] = ["even" if value % 2 == 0 else "odd" for value in values]
assert kept == [20, 20, 30]
assert unique == {1, 2, 3}
assert lookup == {1: 10, 2: 20, 3: 30}
assert list(lazy) == kept
assert labels == ["odd", "even", "even", "odd"]
```

## 5. Minimal Example

**Example A — Tiny**

```python
numbers: list[int] = [1, 2, 3, 4]
squares: list[int] = [number * number for number in numbers if number % 2 == 0]
assert squares == [4, 16]
```

## 6. Step-by-Step Execution

**Example B — Practical:** normalize nonempty inventory labels, preserving their order.

```python
raw: list[str] = [" Tea ", " ", "Coffee"]
labels: list[str] = []
for label in raw:
    if label.strip():
        labels.append(label.strip().lower())
compact: list[str] = [label.strip().lower() for label in raw if label.strip()]
assert labels == compact == ["tea", "coffee"]
```

| Input | Filter result | Transformed value |
|---|---|---|
| `" Tea "` | True | `"tea"` |
| `" "` | False | No output |
| `"Coffee"` | True | `"coffee"` |

The filter runs before the output expression for each item. Comprehension iteration
variables have their own scope; ordinary `for` statements bind in the surrounding scope.

## 7. Comparison

| Form | Result / evaluation | Ordering and duplicates | Good fit |
|---|---|---|---|
| Explicit loop | Statements execute each iteration | Determined by your operations | Branches, side effects, `break` |
| `[f(x) for x in xs]` | Eager list | Input iteration order; repeats kept | Ranked prompt context |
| `{f(x) for x in xs}` | Eager set | No ordering guarantee; unique values | Allowed tool names |
| `{k: v for k, v in pairs}` | Eager dict | First key position; last value per key | Latest local configuration |
| `(f(x) for x in xs)` | Lazy generator | Input iteration order; one-shot | Single-pass processing |

Ordering is only as meaningful as the input order: a list comprehension over a set
does not recover retrieval ranking. See [iterators and generators](../02-iterators-generators/README.md).

## 8. 🎯 AI Engineering Use Case

**Example C — AI Engineering:** local scored hits are already ranked by a retriever.
Keep scores at or above the threshold without sorting or collapsing repeated IDs.

```python
type Hit = tuple[str, float]

def select_hits(hits: list[Hit], minimum: float) -> list[Hit]:
    return [hit for hit in hits if hit[1] >= minimum]

hits: list[Hit] = [("b", 0.85), ("a", 0.4), ("b", 0.95), ("c", 0.7)]
assert select_hits(hits, 0.7) == [("b", 0.85), ("b", 0.95), ("c", 0.7)]
assert select_hits([], 0.7) == []
assert select_hits(hits, 1.0) == []
```

The input order is authoritative, even when scores are not descending. Duplicate IDs
can represent separate chunks; deduplicate only with an explicit identity policy.
This example assumes validated finite scores; input validation is a separate boundary.

## 9. When to Use / When NOT to Use

```text
WHEN TO USE
✅ Good for:
- One clear transformation with a small number of readable filters.
- Building an ordered collection of qualifying retrieval hits.

WHEN NOT TO USE
❌ Avoid when:
- Each iteration needs logging, retries, mutation, or early termination.
- Nested conditions hide the selection policy.

BETTER ALTERNATIVE
Use an explicit loop when steps need names or branching.
Use a generator expression when a consumer needs one pass without a result list.
```

## 10. 🚨 Common Mistakes

**Wrong: expect a dict to retain all repeated hits. Better: keep a list for ranking.**
This runnable example demonstrates the lossy conversion, then the suitable container.

```python
pairs: list[tuple[str, float]] = [("b", 0.85), ("a", 0.8), ("b", 0.95)]
collapsed: dict[str, float] = {key: score for key, score in pairs}
preserved: list[tuple[str, float]] = [pair for pair in pairs]
assert collapsed == {"b": 0.95, "a": 0.8}
assert list(collapsed) == ["b", "a"]
assert len(preserved) == 3
```

The last assignment replaces a key's value without moving its first insertion position.

**Wrong: build a list just to trigger side effects. Better: use a loop.**

```python
source: list[str] = ["a", "b"]
wrong_output: list[str] = []
discarded: list[None] = [wrong_output.append(item) for item in source]
assert discarded == [None, None]

better_output: list[str] = []
for item in source:
    better_output.append(item)
assert better_output == wrong_output == ["a", "b"]
```

**Wrong: expect the iteration name to leak. Better: retain a named result.**

```python
value: int = 99
result: list[int] = [value for value in range(2)]
assert value == 99
assert result == [0, 1]
```

No deliberately failing Python snippets are used in this lesson; wrong approaches above
run successfully and use assertions to demonstrate their unwanted behavior.

## 11. ⚡ Quick Tricks

```python
batches: list[list[str]] = [["a", ""], ["b"]]
flattened: list[str] = [item for batch in batches for item in batch if item]
assert flattened == ["a", "b"]

equivalent: list[str] = []
for batch in batches:
    for item in batch:
        if item:
            equivalent.append(item)
assert equivalent == flattened
```

Read nested `for` clauses left to right, in the same order as nested loops. Two simple
clauses can be readable; use a loop or helper function once nesting obscures intent.

## 12. Performance Considerations

For n inputs and k accepted items, a simple filter/transform scans O(n) inputs and
stores O(k) results. A generator avoids the result list, but retains references to its
iteration state and does not make an already materialized input list disappear.
Set/dict insertion is average O(1), subject to hashing costs and collisions.

```python
from collections.abc import Iterator

stream: Iterator[int] = (number * number for number in range(4))
assert next(stream) == 0
assert list(stream) == [1, 4, 9]
assert list(stream) == []
```

A generator is exhausted after consumption. Use a list for repeated access, or create
a fresh generator from a repeatable input. Measure realistic work before choosing syntax
for a small speed difference; remote inference latency usually dominates these transforms.

## 13. 🎤 Interview Questions

**Filter versus conditional expression?** A trailing `if` excludes items; `a if test
else b` produces one of two values for every item that reaches the expression.

**Does a comprehension sort?** No. Lists and generators follow input iteration order.
Sets provide no ranking guarantee; dicts retain key insertion order.

**What happens with duplicate dict keys?** The last value wins; the original key
position stays. Use a list when repeated hits are meaningful.

**Does the loop name escape a comprehension?** No. The comprehension iteration target
does not replace the same name in the surrounding scope.

## 14. 🛠 Mini Exercise

Given ranked `(document_id, score)` pairs, return IDs whose scores are at least 0.7.
Preserve order and repeated IDs. Then consume an equivalent generator twice.

```text
[]                                      -> []
[("b", 0.8), ("a", 0.1), ("b", 0.9)]   -> ["b", "b"]
generator first consumption              -> ["b", "b"]
generator second consumption             -> []
```

Explain why a set would violate the output contract. The runnable script below checks
the same policy and generator exhaustion.

## 15. Real-World / Runnable Code Example

Run the [standalone script](examples/comprehensions.py) from the repository root:

```bash
python 00-python-foundation-review/examples/comprehensions.py
```

```text
Selected hits: [('b', 0.85), ('b', 0.95), ('c', 0.7)]
Comprehension checks passed.
```

Assertions cover empty input, all-rejected input, duplicate keys, rank preservation,
scope, branching, flattening, and one-shot generator consumption.

## 16. Cheat Sheet

| Need | Form | Remember |
|---|---|---|
| Filter and transform | `[f(x) for x in xs if keep(x)]` | Filter before transform |
| Choose output value | `[a if test(x) else b for x in xs]` | Does not filter |
| Unique values | `{f(x) for x in xs}` | No ranking guarantee |
| Map keys to values | `{k: v for k, v in pairs}` | Last value wins |
| Lazy results | `(f(x) for x in xs)` | Single consumption |
| Side effects / early exit | Explicit `for` | Use `continue` / `break` |
| Nested iteration | `for outer ... for inner ...` | Same order as loops |

Back to [foundation review](README.md).
