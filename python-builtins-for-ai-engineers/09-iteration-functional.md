# 09 — Iteration & Functional Tools

High-performance iteration, specialized containers, and functional operators — the workhorse layer for processing data at scale in AI pipelines.

---

## `itertools`

**Import:** `from itertools import islice, chain, batched`

**When to use:** Chunk large datasets into batches for embedding APIs, merge multiple result streams, take slices without loading everything into memory.

**Mental model:** A factory assembly line — it produces items one at a time through composable stages, so you can process a million documents without holding them all in memory.

```python
from itertools import islice, chain
from typing import Iterator

def batched(iterable: Iterator, n: int) -> Iterator[tuple]:
    """Chunk an iterable into batches of size n (stdlib in 3.12+)."""
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch

def embed_corpus(documents: list[str], batch_size: int = 100) -> list[list[float]]:
    """Chunk a 100k document corpus into batches for the embedding API."""
    all_embeddings: list[list[float]] = []
    for i, batch in enumerate(batched(iter(documents), batch_size)):
        # In production: embeddings = await client.embeddings.create(input=batch)
        embeddings = [[0.1] * 384 for _ in batch]  # simulated
        all_embeddings.extend(embeddings)
        if (i + 1) % 100 == 0:
            print(f"Embedded {(i + 1) * batch_size} documents...")
    return all_embeddings

# Process 100k documents in memory-efficient 100-doc batches
corpus = [f"Document {i}: content about topic..." for i in range(1000)]
vectors = embed_corpus(corpus, batch_size=100)
print(f"Embedded {len(vectors)} documents, dim={len(vectors[0])}")
```

**Gotcha:** `itertools` produces lazy iterators — they're single-pass. Calling `list()` on a consumed iterator returns `[]`. Store the result if you need it twice.

---

## `collections.Counter`

**Import:** `from collections import Counter`

**When to use:** Token frequency analysis on LLM outputs, distribution analysis of tool calls, top-k scoring.

**Mental model:** A tally counter — it counts occurrences of each item and gives you instant access to the most common ones.

```python
from collections import Counter

def analyze_token_distribution(responses: list[str]) -> dict[str, object]:
    """Analyze token frequency patterns across LLM outputs."""
    all_tokens: list[str] = []
    for response in responses:
        all_tokens.extend(response.lower().split())

    freq = Counter(all_tokens)
    total = sum(freq.values())

    return {
        "total_tokens": total,
        "unique_tokens": len(freq),
        "top_10": freq.most_common(10),
        "vocabulary_richness": round(len(freq) / total, 4) if total else 0,
        "hapax_legomena": sum(1 for count in freq.values() if count == 1),
    }

responses = [
    "RAG combines retrieval with generation for better accuracy",
    "Vector search enables semantic retrieval over large corpora",
    "Embeddings capture semantic meaning for retrieval and ranking",
]
analysis = analyze_token_distribution(responses)
print(f"Unique tokens: {analysis['unique_tokens']}")
print(f"Top 5: {analysis['top_10'][:5]}")
```

**Gotcha:** `Counter` subtraction drops zero and negative counts by default. Use `counter.subtract()` to keep them, or `+counter` to filter after arithmetic.

---

## `collections.defaultdict`

**Import:** `from collections import defaultdict`

**When to use:** Group results by category — organize tool outputs, cluster search results by source, aggregate metrics by model.

**Mental model:** A filing cabinet that auto-creates folders — when you open a drawer that doesn't exist yet, it materializes an empty one instead of throwing a `KeyError`.

```python
from collections import defaultdict
from typing import Any

def group_tool_results(
    results: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Group agent tool results by category for structured output."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        category = result.get("source", "unknown")
        grouped[category].append({
            "content": result["content"],
            "score": result.get("relevance_score", 0.0),
        })

    # Sort each group by relevance score
    for category in grouped:
        grouped[category].sort(key=lambda x: x["score"], reverse=True)
    return dict(grouped)

tool_results = [
    {"source": "web_search", "content": "RAG overview", "relevance_score": 0.9},
    {"source": "vector_db", "content": "Embedding tutorial", "relevance_score": 0.85},
    {"source": "web_search", "content": "LLM comparison", "relevance_score": 0.7},
    {"source": "vector_db", "content": "Chunking strategies", "relevance_score": 0.95},
    {"source": "code_search", "content": "RAG implementation", "relevance_score": 0.88},
]

grouped = group_tool_results(tool_results)
for source, items in grouped.items():
    print(f"{source}: {len(items)} results, top score={items[0]['score']}")
```

**Gotcha:** `defaultdict(list)` creates a new list on every missing key access — even `if key in d` followed by `d[key]` creates the entry. Use `d.get(key)` when you don't want auto-creation.

---

## `operator`

**Import:** `from operator import itemgetter, attrgetter, methodcaller`

**When to use:** Clean key functions for sorting, filtering, and extracting fields from structured results — avoids lambda clutter in data pipelines.

**Mental model:** Pre-built micro-functions for common operations — instead of `lambda x: x["score"]`, use `itemgetter("score")`. Same result, better readability, faster execution.

```python
from operator import itemgetter, attrgetter
from dataclasses import dataclass

@dataclass
class SearchResult:
    content: str
    score: float
    source: str

def rank_and_filter(
    results: list[dict[str, object]], min_score: float = 0.5
) -> list[dict[str, object]]:
    """Rank search results by score and filter below threshold."""
    filtered = [r for r in results if r["score"] >= min_score]
    return sorted(filtered, key=itemgetter("score"), reverse=True)

results = [
    {"content": "About RAG", "score": 0.92, "source": "docs"},
    {"content": "Unrelated", "score": 0.31, "source": "web"},
    {"content": "Embeddings guide", "score": 0.87, "source": "docs"},
    {"content": "Chunking tips", "score": 0.78, "source": "blog"},
]

ranked = rank_and_filter(results, min_score=0.5)
for r in ranked:
    print(f"[{r['score']:.2f}] {r['content']}")
# [0.92] About RAG
# [0.87] Embeddings guide
# [0.78] Chunking tips
```

**Gotcha:** `itemgetter` raises `KeyError`/`IndexError` on missing keys — it's not forgiving like `.get()`. Ensure your data is clean before using it as a sort key.
