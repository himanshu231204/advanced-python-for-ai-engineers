# 04 — Loops & Iteration

Looping constructs and flow control keywords — how AI pipelines iterate over batches, poll for results, and control execution inside loops.

---

## `for`

**Syntax:** `for item in iterable:` (iterate over a sequence)

**When to use:** Process batches of embeddings, iterate over conversation messages, walk through retrieved documents, run multiple prompts through an LLM.

**Mental model:** A conveyor belt — items arrive one at a time, you process each one, and the belt stops when there's nothing left. Python's `for` always iterates over something (no C-style `for(i=0; i<n; i++)`).

```python
from typing import Any

def batch_embed(texts: list[str], batch_size: int = 3) -> list[list[float]]:
    """Process texts in batches for embedding."""
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # Simulate embedding API call
        embeddings = [[0.1 * j for j in range(4)] for _ in batch]
        all_embeddings.extend(embeddings)
        print(f"Embedded batch {i // batch_size + 1}: {len(batch)} texts")
    return all_embeddings

texts = ["What is RAG?", "Explain embeddings", "Define LLM",
         "What is HNSW?", "Explain attention"]
results = batch_embed(texts, batch_size=2)
print(f"Total embeddings: {len(results)}")

# for with dict — iterate over conversation history
messages: list[dict[str, str]] = [
    {"role": "user", "content": "What is RAG?"},
    {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation..."},
    {"role": "user", "content": "Show me code"},
]
for msg in messages:
    prefix = ">>" if msg["role"] == "user" else "<<"
    print(f"  {prefix} {msg['content'][:40]}")
```

**Gotcha:** Modifying a list while iterating over it leads to skipped items or infinite loops. Iterate over a copy (`for item in items[:]`) or build a new list instead.

---

## `while`

**Syntax:** `while condition:` (loop until condition is falsy)

**When to use:** Polling loops — wait for async job completion, retry with backoff until success, agent reasoning loops that run until a stop condition.

**Mental model:** A "keep going" alarm clock — it checks the condition before each lap. Unlike `for`, it doesn't know how many laps there will be — it just keeps running until the alarm says "stop."

```python
import time
import random

def poll_with_backoff(job_id: str, max_wait: float = 30.0) -> str:
    """Poll for job completion with exponential backoff."""
    wait = 1.0
    total_waited = 0.0

    while total_waited < max_wait:
        # Simulate checking job status
        status = random.choice(["running", "running", "completed"])
        print(f"  [{total_waited:.0f}s] Job {job_id}: {status}")

        if status == "completed":
            return f"Job {job_id} finished after {total_waited:.0f}s"

        time.sleep(min(wait, 0.01))  # short sleep for demo
        total_waited += wait
        wait = min(wait * 2, 10.0)  # exponential backoff, cap at 10s

    return f"Job {job_id} timed out after {max_wait}s"

random.seed(42)
print(poll_with_backoff("embed-001", max_wait=20.0))

# Agent reasoning loop — run until the agent decides to stop
def agent_loop(query: str, max_steps: int = 5) -> str:
    step = 0
    context = query
    while step < max_steps:
        step += 1
        # Simulate agent deciding whether to continue
        if len(context) > 50:
            return f"Final answer after {step} steps: {context[:60]}..."
        context += f" -> step {step} result"
    return f"Stopped after {max_steps} steps: {context[:60]}..."

print(agent_loop("What is the capital of France?"))
```

**Gotcha:** Forgetting to update the loop variable creates an infinite loop. Always ensure the condition will eventually become falsy — add a max-iteration safety check or a timeout.

---

## `break`

**Syntax:** `break` (exit the nearest enclosing loop immediately)

**When to use:** Early termination — stop searching once a good enough result is found, exit a polling loop on success, bail out of an agent loop when a stop token is received.

**Mental model:** The emergency exit — you're in a loop and something happens that means you don't need to keep going. `break` jumps you straight out of the loop body.

```python
def find_best_chunk(chunks: list[dict[str, float]], threshold: float = 0.85) -> dict[str, float] | None:
    """Find the first chunk that exceeds the relevance threshold."""
    for chunk in chunks:
        print(f"  Checking: score={chunk['score']:.2f}")
        if chunk["score"] >= threshold:
            print(f"  Found! Skipping remaining {len(chunks)} chunks")
            break
    else:
        # for/else: runs only if break was NOT hit
        print("  No chunk met the threshold")
        return None
    return chunk

chunks = [
    {"score": 0.6, "text": "intro"},
    {"score": 0.92, "text": "relevant section"},
    {"score": 0.88, "text": "also relevant"},
]
result = find_best_chunk(chunks)
print(f"Result: {result}")

# break in a streaming response consumer
def consume_stream(tokens: list[str]) -> str:
    """Consume tokens until a stop sequence is found."""
    output: list[str] = []
    for token in tokens:
        if token == "<|END|>":
            break
        output.append(token)
    return "".join(output)

tokens = ["Hello", " world", "!", "<|END|>", "ignored", "tokens"]
print(consume_stream(tokens))  # Hello world!
```

**Gotcha:** `break` only exits the *innermost* loop. In nested loops, you need a flag variable, an exception, or a refactor into a function with `return` to break out of multiple levels.

---

## `continue`

**Syntax:** `continue` (skip to the next iteration of the nearest loop)

**When to use:** Skip invalid items in a batch — filter out empty documents, skip failed API responses, ignore malformed messages in a conversation history.

**Mental model:** The "next!" button — instead of leaving the loop entirely, you just skip the current item and move on to the next one. The loop keeps running.

```python
from typing import Any

def process_documents(docs: list[dict[str, Any]]) -> list[str]:
    """Process documents, skipping invalid ones."""
    results: list[str] = []
    for i, doc in enumerate(docs):
        if not doc.get("content"):
            print(f"  Skipping doc {i}: empty content")
            continue
        if doc.get("language") != "en":
            print(f"  Skipping doc {i}: language={doc.get('language')}")
            continue
        if len(doc["content"]) > 50_000:
            print(f"  Skipping doc {i}: too long ({len(doc['content'])} chars)")
            continue
        # Only valid docs reach here
        results.append(doc["content"][:100])
    return results

docs: list[dict[str, Any]] = [
    {"content": "RAG overview...", "language": "en"},
    {"content": "", "language": "en"},
    {"content": "Guide technique...", "language": "fr"},
    {"content": "Embeddings explained...", "language": "en"},
]
valid = process_documents(docs)
print(f"Processed {len(valid)} of {len(docs)} documents")

# continue in retry logic — skip failed items, keep going
def batch_classify(items: list[str]) -> list[tuple[str, str]]:
    """Classify items, skipping any that fail."""
    results: list[tuple[str, str]] = []
    for item in items:
        if not item.strip():
            continue
        label = "positive" if "good" in item.lower() else "negative"
        results.append((item, label))
    return results

labels = batch_classify(["Good result", "", "Bad outcome", "  ", "Good match"])
print(f"Classified: {labels}")
```

**Gotcha:** `continue` inside a `try`/`finally` block still executes the `finally` clause before jumping to the next iteration. This can cause surprising behavior if `finally` has side effects.

---

## `pass`

**Syntax:** `pass` (do nothing — a no-op placeholder)

**When to use:** Stub out classes and functions during development, define empty exception handlers (intentionally ignore specific errors), create abstract-like base classes.

**Mental model:** A blank page in a notebook — it holds the space so the structure is valid, but says "nothing here yet." Python's syntax requires a body in every block, so `pass` fills that requirement.

```python
from typing import Any

# Stub out agent tools during development
class WebSearchTool:
    """TODO: Implement web search integration."""
    def run(self, query: str) -> str:
        pass  # Will return search results

class CalculatorTool:
    """TODO: Implement calculator."""
    def run(self, expression: str) -> str:
        pass

# Intentionally ignore specific exceptions
def safe_parse_score(raw: str) -> float:
    """Parse a score, returning 0.0 for any unparseable input."""
    try:
        return float(raw)
    except (ValueError, TypeError):
        pass
    return 0.0

print(safe_parse_score("0.95"))   # 0.95
print(safe_parse_score("N/A"))    # 0.0
print(safe_parse_score(""))       # 0.0

# Abstract base pattern — define the interface, subclasses fill in
class BaseLLMProvider:
    def complete(self, prompt: str) -> str:
        raise NotImplementedError

    def stream(self, prompt: str):
        raise NotImplementedError

    def on_error(self, error: Exception) -> None:
        pass  # Optional hook — subclasses can override or ignore
```

**Gotcha:** Don't use `pass` to silently swallow important exceptions — `except Exception: pass` hides bugs. Only use it when you've deliberately decided to ignore a *specific* exception type and documented why (or when stubbing code you'll fill in shortly).
