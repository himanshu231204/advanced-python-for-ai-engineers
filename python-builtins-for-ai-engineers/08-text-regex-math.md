# 08 — Text, Regex & Math

Text processing, pattern matching, hashing, and numerical operations — the utility layer for NLP pipelines and data integrity.

---

## `re`

**Import:** `import re`

**When to use:** Extract structured data from LLM outputs — parse tool calls, extract code blocks, validate response formats, clean text before embedding.

**Mental model:** A precision scalpel for text — it cuts out exactly the patterns you describe, from a sea of unstructured characters.

```python
import re

def extract_tool_calls(llm_output: str) -> list[dict[str, str]]:
    """Extract tool calls from LLM output in <tool>...</tool> format."""
    pattern = r"<tool\s+name=\"(\w+)\">(.*?)</tool>"
    matches = re.findall(pattern, llm_output, re.DOTALL)
    return [{"name": name, "args": args.strip()} for name, args in matches]

def extract_code_blocks(markdown: str) -> list[dict[str, str]]:
    """Extract fenced code blocks with language labels."""
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, markdown, re.DOTALL)
    return [{"language": lang or "text", "code": code.strip()} for lang, code in matches]

llm_response = """
I'll search for that information.
<tool name="web_search">{"query": "RAG best practices 2024"}</tool>
Let me also check the docs.
<tool name="read_file">{"path": "/docs/rag.md"}</tool>
"""

tools = extract_tool_calls(llm_response)
for t in tools:
    print(f"Tool: {t['name']}, Args: {t['args']}")
```

**Gotcha:** Use `re.DOTALL` when your pattern needs to match across newlines — without it, `.` doesn't match `\n` and multi-line content silently fails to match.

---

## `string`

**Import:** `import string`

**When to use:** Template-based prompt construction, text normalization, character-set operations for preprocessing.

**Mental model:** A toolbox of text constants and a simple template engine — when f-strings are too dynamic and Jinja is overkill.

```python
import string

def build_prompt_template(template: str, **variables: str) -> str:
    """Safe prompt template that raises on missing variables (unlike f-strings)."""
    tpl = string.Template(template)
    return tpl.substitute(variables)  # KeyError if a variable is missing

def normalize_for_embedding(text: str) -> str:
    """Normalize text before generating embeddings."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = " ".join(text.split())  # collapse whitespace
    return text

# Prompt template with safe substitution
prompt = build_prompt_template(
    "You are a $role. Answer this question about $topic: $question",
    role="helpful AI assistant",
    topic="vector databases",
    question="What is HNSW?",
)
print(prompt)

# Text normalization for consistent embedding
raw = "  Hello, World!!!  What's    up?  "
clean = normalize_for_embedding(raw)
print(clean)  # "hello world whats up"
```

**Gotcha:** `string.Template.substitute()` raises `KeyError` on missing keys (which is often what you want for prompts). Use `safe_substitute()` only when you intentionally want to leave placeholders unfilled.

---

## `hashlib`

**Import:** `import hashlib`

**When to use:** Deduplicate documents in your corpus, create cache keys for LLM responses, verify downloaded model file integrity.

**Mental model:** A fingerprint machine — it converts any data into a fixed-size unique identifier. Same input always gives same output; different inputs (virtually) never collide.

```python
import hashlib
import json
from typing import Any

def content_hash(text: str) -> str:
    """Generate a content-addressable hash for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def cache_key_for_llm_call(model: str, messages: list[dict[str, str]],
                            temperature: float) -> str:
    """Deterministic cache key for an LLM API call."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:24]

# Deduplication
docs = ["Hello world", "Hello world", "Different text"]
unique = {content_hash(d): d for d in docs}
print(f"Deduped: {len(docs)} → {len(unique)} documents")

# Cache key
key = cache_key_for_llm_call(
    "claude-3-opus",
    [{"role": "user", "content": "What is RAG?"}],
    temperature=0.0,
)
print(f"Cache key: {key}")
```

**Gotcha:** Hash truncation increases collision probability. 16 hex chars (64 bits) is fine for caching; use full SHA-256 (64 hex chars) for security-critical deduplication.

---

## `math` / `statistics`

**Import:** `import math` / `import statistics`

**When to use:** Cosine similarity for embeddings, statistical analysis of eval results, numerical operations in scoring functions.

**Mental model:** `math` gives you the calculator operations (sqrt, log, dot products). `statistics` gives you the spreadsheet summary functions (mean, median, stdev).

```python
import math
import statistics

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two embedding vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

def eval_summary(scores: list[float]) -> dict[str, float]:
    """Statistical summary of model evaluation scores."""
    return {
        "mean": round(statistics.mean(scores), 3),
        "median": round(statistics.median(scores), 3),
        "stdev": round(statistics.stdev(scores), 3) if len(scores) > 1 else 0.0,
        "p95": round(sorted(scores)[int(len(scores) * 0.95)], 3),
    }

# Embedding similarity
emb_a = [0.1, 0.3, 0.5, 0.7]
emb_b = [0.2, 0.4, 0.6, 0.8]
print(f"Similarity: {cosine_similarity(emb_a, emb_b):.4f}")  # 0.9969

# Eval results analysis
scores = [0.82, 0.91, 0.76, 0.88, 0.95, 0.73, 0.89, 0.84, 0.90, 0.87]
summary = eval_summary(scores)
print(f"Eval: mean={summary['mean']}, stdev={summary['stdev']}")
```

**Gotcha:** `statistics.stdev()` requires at least 2 data points — it raises `StatisticsError` on a single-element list. Guard with a length check.

---

## `random` / `secrets`

**Import:** `import random` / `import secrets`

**When to use:** `random` for reproducible sampling (eval subsets, A/B splits, data augmentation). `secrets` for security-sensitive generation (API keys, tokens, session IDs).

**Mental model:** `random` is a deck of cards you can shuffle the same way every time (seeded). `secrets` is a casino-grade RNG — unpredictable, non-reproducible, safe for security.

```python
import random
import secrets

def sample_eval_subset(
    dataset: list[dict[str, str]], n: int, seed: int = 42
) -> list[dict[str, str]]:
    """Reproducible random sample for evaluation consistency."""
    rng = random.Random(seed)
    return rng.sample(dataset, min(n, len(dataset)))

def generate_api_credentials() -> dict[str, str]:
    """Generate secure API key and session token."""
    return {
        "api_key": f"sk-{secrets.token_urlsafe(32)}",
        "session_id": secrets.token_hex(16),
        "webhook_secret": secrets.token_urlsafe(24),
    }

# Reproducible eval sampling
dataset = [{"id": str(i), "text": f"doc_{i}"} for i in range(1000)]
subset = sample_eval_subset(dataset, n=50)
print(f"Sampled {len(subset)} docs, first: {subset[0]['id']}")

# Secure credential generation
creds = generate_api_credentials()
print(f"API key: {creds['api_key'][:10]}...")
```

**Gotcha:** Never use `random` for security purposes — it's deterministic and predictable. API keys, tokens, and passwords must use `secrets`.
