# 05 — Functions & Lambdas

Function definition, return values, anonymous functions, and generators — the core building blocks of every AI pipeline, tool, and agent.

---

## `def`

**Syntax:** `def name(params) -> ReturnType:` (define a function)

**When to use:** Every reusable piece of logic — tool implementations, pipeline steps, request handlers, data transformations, LLM call wrappers.

**Mental model:** A recipe card — you write it once (define), and anyone can cook the dish later (call). The parameters are the ingredients, the body is the instructions, and the return value is the finished dish.

```python
from typing import Any

def build_rag_prompt(
    query: str,
    retrieved_docs: list[str],
    system_instruction: str = "Answer based only on the provided context.",
    max_context_chars: int = 5000,
) -> dict[str, Any]:
    """Build a RAG prompt with retrieved context."""
    context = "\n---\n".join(retrieved_docs)[:max_context_chars]
    return {
        "system": system_instruction,
        "messages": [
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ],
        "metadata": {"doc_count": len(retrieved_docs), "context_len": len(context)},
    }

docs = ["RAG retrieves relevant documents...", "Embeddings map text to vectors..."]
prompt = build_rag_prompt("What is RAG?", docs)
print(f"System: {prompt['system']}")
print(f"Docs used: {prompt['metadata']['doc_count']}")

# Keyword-only parameters (after *) — prevents positional mistakes
def call_llm(prompt: str, *, model: str = "claude-3", temperature: float = 0.7) -> str:
    return f"[{model} t={temperature}] {prompt[:30]}..."

print(call_llm("Explain RAG", model="gpt-4", temperature=0.0))
```

**Gotcha:** Mutable default arguments are shared across calls — `def f(items=[])` reuses the same list. Always use `None` as default and create inside the function: `def f(items: list | None = None): items = items or []`.

---

## `return`

**Syntax:** `return value` (exit function and send back a result)

**When to use:** Send results back from tool functions, pipeline steps, validators, and parsers. Multiple return points enable guard-clause patterns.

**Mental model:** The delivery truck — once the recipe is done, `return` ships the result back to whoever called the function. Without it, the function implicitly returns `None`.

```python
from typing import Any

def extract_tool_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool calls from an LLM response, with early returns for invalid data."""
    if not response:
        return []

    content = response.get("content")
    if not content:
        return []

    # Guard clause pattern: each check returns early on failure
    tool_calls = response.get("tool_calls")
    if not tool_calls:
        return []

    return [
        {"name": tc["name"], "args": tc.get("arguments", {})}
        for tc in tool_calls
        if "name" in tc
    ]

# Multiple return values via tuple (common in Python)
def score_and_rank(docs: list[dict[str, float]]) -> tuple[float, int]:
    """Return best score and how many docs were above threshold."""
    if not docs:
        return 0.0, 0
    best = max(d["score"] for d in docs)
    above = sum(1 for d in docs if d["score"] > 0.7)
    return best, above

best_score, count = score_and_rank([
    {"score": 0.9}, {"score": 0.6}, {"score": 0.8}
])
print(f"Best: {best_score}, Above threshold: {count}")  # Best: 0.9, Above threshold: 2

# Early return in validation — cleaner than nested if/else
def validate_request(req: dict[str, Any]) -> str | None:
    """Return error message, or None if valid."""
    if "model" not in req:
        return "Missing required field: model"
    if "messages" not in req:
        return "Missing required field: messages"
    if not req["messages"]:
        return "Messages array cannot be empty"
    return None  # All checks passed

error = validate_request({"model": "claude-3"})
print(f"Validation: {error or 'OK'}")
```

**Gotcha:** `return` without a value (or falling off the end of a function) returns `None`. In a function that should return data, a missing `return` is a silent bug — type-check your code to catch functions that accidentally return `None`.

---

## `lambda`

**Syntax:** `lambda params: expression` (anonymous single-expression function)

**When to use:** Short callbacks and key functions — sorting documents by score, filtering items, simple transformations passed to `map`/`filter`/`sorted`.

**Mental model:** A sticky note function — too small for its own recipe card, so you write it inline. It can only hold one expression (no statements, no assignments, no multi-line logic).

```python
from typing import Any

# Sort retrieved documents by relevance score (descending)
docs = [
    {"title": "RAG Guide", "score": 0.82},
    {"title": "Embeddings Deep Dive", "score": 0.95},
    {"title": "Intro to LLMs", "score": 0.71},
]
ranked = sorted(docs, key=lambda d: d["score"], reverse=True)
for d in ranked:
    print(f"  {d['score']:.2f} — {d['title']}")

# Filter out low-confidence tool calls
tool_results: list[dict[str, Any]] = [
    {"tool": "search", "confidence": 0.9, "result": "Paris"},
    {"tool": "calc", "confidence": 0.3, "result": "error"},
    {"tool": "search", "confidence": 0.8, "result": "France"},
]
confident = list(filter(lambda r: r["confidence"] >= 0.7, tool_results))
print(f"High-confidence results: {len(confident)}")

# Lambda in a dispatch table
handlers: dict[str, Any] = {
    "upper": lambda text: text.upper(),
    "lower": lambda text: text.lower(),
    "strip": lambda text: text.strip(),
    "word_count": lambda text: len(text.split()),
}
for name, fn in handlers.items():
    print(f"  {name}: {fn('  Hello World  ')}")
```

**Gotcha:** Lambda is limited to a single expression — no `if`/`else` statements (but ternary `a if cond else b` works), no assignments, no try/except. If you need more than one line, use `def`. Also avoid storing lambdas in variables (`f = lambda x: x + 1`) — that's just a worse `def f(x): return x + 1`.

---

## `yield`

**Syntax:** `yield value` (produce a value and suspend the generator)

**When to use:** Stream results lazily — token-by-token LLM responses, paginated API results, large dataset processing without loading everything into memory.

**Mental model:** A "pause and hand over" button — unlike `return` which exits the function forever, `yield` hands a value to the caller and freezes the function in place. Next time the caller asks, it picks up right where it left off.

```python
from typing import Generator, Any

def stream_tokens(text: str, chunk_size: int = 5) -> Generator[str, None, None]:
    """Simulate streaming LLM output token by token."""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        yield chunk

# Lazy iteration — only generates chunks as needed
for chunk in stream_tokens("RAG combines retrieval with generation to produce grounded answers"):
    print(f"  chunk: {chunk!r}")

# yield in a paginated API reader
def paginated_fetch(total_items: int, page_size: int = 10) -> Generator[list[dict[str, int]], None, None]:
    """Yield pages of results lazily."""
    for offset in range(0, total_items, page_size):
        page = [{"id": i, "offset": offset} for i in range(offset, min(offset + page_size, total_items))]
        yield page

for page_num, page in enumerate(paginated_fetch(25, page_size=10)):
    print(f"  Page {page_num + 1}: {len(page)} items")

# yield from — delegate to a sub-generator
def all_chunks(documents: list[str]) -> Generator[str, None, None]:
    """Stream chunks from multiple documents."""
    for doc in documents:
        yield from stream_tokens(doc, chunk_size=3)

docs = ["Embeddings map text", "Vectors enable search"]
chunks = list(all_chunks(docs))
print(f"Total chunks from {len(docs)} docs: {len(chunks)}")
```

**Gotcha:** A generator can only be consumed once — after it's exhausted, iterating again yields nothing. If you need to iterate multiple times, either convert to a list (`list(gen)`) or call the generator function again. This is a common bug in pipelines that reuse a generator variable.
