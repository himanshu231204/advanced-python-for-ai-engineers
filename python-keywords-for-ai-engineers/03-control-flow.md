# 03 — Control Flow

Conditional branching and structural pattern matching — how AI agents decide which path to take, which tool to call, and how to route requests.

---

## `if`

**Syntax:** `if condition:` (starts a conditional block)

**When to use:** Every decision point — routing agent actions, checking API response status, gating feature flags, validating inputs before LLM calls.

**Mental model:** A fork in the road — your code checks a signpost (the condition) and takes the matching path. Everything indented under `if` only runs when the sign says "yes."

```python
from typing import Any

def route_agent_action(intent: str, context: dict[str, Any]) -> str:
    """Route an agent to the right action based on classified intent."""
    if intent == "search":
        query = context.get("query", "")
        return f"Searching for: {query}"

    if intent == "summarize":
        text = context.get("text", "")
        return f"Summarizing {len(text)} chars..."

    if intent == "code":
        return "Generating code..."

    return "I'm not sure how to help with that."

# Inline conditional (ternary) — common in AI pipelines
temperature = 0.0
mode = "deterministic" if temperature == 0.0 else "creative"
print(f"Mode: {mode}")  # deterministic

# Guard clause pattern — validate early, return early
def call_llm(prompt: str, max_tokens: int = 4096) -> str:
    if not prompt.strip():
        return ""
    if max_tokens <= 0:
        return ""
    return f"Response to: {prompt[:30]}... (max {max_tokens} tokens)"

print(call_llm("What is RAG?"))
print(call_llm("  "))  # empty string — guard caught it
```

**Gotcha:** Python has no `switch` statement (use `match`/`case` in 3.10+ or a dict dispatch). Long `if`/`elif` chains work but become hard to maintain past ~5 branches — consider a dict mapping for clean tool dispatch.

---

## `elif`

**Syntax:** `elif condition:` (else-if branch)

**When to use:** Multi-branch decisions where conditions are mutually exclusive — HTTP status handling, model selection, retry strategy selection.

**Mental model:** Extra doors in a hallway — Python tries each door in order and enters the first one that opens. Once inside, it skips all remaining doors.

```python
def handle_api_response(status_code: int, body: str) -> str:
    """Handle LLM API response by status code."""
    if status_code == 200:
        return f"Success: {body[:50]}"
    elif status_code == 429:
        return "Rate limited — backing off"
    elif status_code == 500:
        return "Server error — retrying with exponential backoff"
    elif status_code == 401:
        return "Authentication failed — check API key"
    elif status_code == 400:
        return f"Bad request: {body[:100]}"
    else:
        return f"Unexpected status: {status_code}"

print(handle_api_response(200, "Hello, I'm Claude..."))
print(handle_api_response(429, ""))
print(handle_api_response(503, "Service unavailable"))

def select_model(task: str, budget: str) -> str:
    """Pick the right model based on task complexity and budget."""
    if task == "embedding" and budget == "low":
        return "text-embedding-3-small"
    elif task == "embedding":
        return "text-embedding-3-large"
    elif task == "chat" and budget == "low":
        return "claude-haiku"
    elif task == "chat":
        return "claude-sonnet"
    elif task == "reasoning":
        return "claude-opus"
    else:
        return "claude-sonnet"

print(select_model("chat", "low"))       # claude-haiku
print(select_model("reasoning", "high")) # claude-opus
```

**Gotcha:** Order matters — Python evaluates `elif` branches top to bottom and takes the first match. Put the most specific conditions first, or a broader condition will shadow a narrower one below it.

---

## `else`

**Syntax:** `else:` (catch-all branch after `if`/`elif`, `for`/`while`, or `try`)

**When to use:** Default/fallback actions — what to do when no condition matched, when a loop completed without `break`, or when no exception was raised.

**Mental model:** The safety net — it catches everything that fell through all the conditions above. On loops, it's more like a "congratulations, you finished" handler.

```python
from typing import Any

def classify_confidence(score: float) -> str:
    """Classify LLM confidence score into actionable tiers."""
    if score >= 0.9:
        return "high — auto-approve"
    elif score >= 0.7:
        return "medium — human review"
    else:
        return "low — reject and retry"

# else on a for loop — runs if no break occurred
def find_relevant_doc(query: str, docs: list[dict[str, Any]]) -> str:
    """Find first doc above threshold, or report failure."""
    for doc in docs:
        if doc["score"] > 0.8:
            return f"Found: {doc['title']} (score={doc['score']})"
    else:
        return "No document met the relevance threshold"

docs = [
    {"title": "RAG Guide", "score": 0.6},
    {"title": "Embeddings 101", "score": 0.5},
]
print(find_relevant_doc("RAG", docs))  # No document met...

docs.append({"title": "Advanced RAG", "score": 0.95})
print(find_relevant_doc("RAG", docs))  # Found: Advanced RAG

# else on try — runs only if no exception was raised
def safe_parse_json(raw: str) -> dict[str, Any] | None:
    import json
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("Failed to parse LLM output as JSON")
        return None
    else:
        print(f"Parsed successfully: {len(data)} keys")
        return data

safe_parse_json('{"model": "claude"}')  # Parsed successfully: 1 keys
safe_parse_json('not json')              # Failed to parse...
```

**Gotcha:** `for/else` and `while/else` are confusing — the `else` block runs when the loop completes *normally* (no `break`), not when the iterable is empty. Many experienced Python developers avoid `for/else` for readability; a flag variable or early `return` is often clearer.

---

## `match`

**Syntax:** `match subject:` (structural pattern matching — Python 3.10+)

**When to use:** Dispatch on complex structures — route tool calls by type, parse LLM structured output, handle different message formats in agent protocols.

**Mental model:** A mail sorting machine — it looks at the shape of each package (not just a label) and routes it to the right bin. Unlike `if`/`elif`, it can destructure and bind variables from the matched structure in one step.

```python
from typing import Any

def handle_tool_call(tool_call: dict[str, Any]) -> str:
    """Dispatch agent tool calls using structural pattern matching."""
    match tool_call:
        case {"name": "search", "args": {"query": query}}:
            return f"Searching: {query}"
        case {"name": "calculate", "args": {"expression": expr}}:
            return f"Computing: {expr}"
        case {"name": "code", "args": {"language": lang, "code": code}}:
            return f"Running {lang}: {code[:30]}..."
        case {"name": name, "args": args}:
            return f"Unknown tool: {name} with {args}"
        case _:
            return "Invalid tool call format"

# Pattern matching destructures the dict and binds variables
print(handle_tool_call({"name": "search", "args": {"query": "Python asyncio"}}))
print(handle_tool_call({"name": "calculate", "args": {"expression": "2+2"}}))
print(handle_tool_call({"name": "unknown_tool", "args": {}}))
print(handle_tool_call("not a dict"))

# Match on message types in an agent protocol
def process_message(msg: dict[str, Any]) -> str:
    match msg:
        case {"role": "user", "content": str(text)}:
            return f"User says: {text[:50]}"
        case {"role": "assistant", "content": str(text), "tool_calls": list(calls)}:
            return f"Assistant responded with {len(calls)} tool calls"
        case {"role": "tool", "name": name, "content": content}:
            return f"Tool {name} returned: {str(content)[:50]}"
        case _:
            return f"Unknown message format: {msg.get('role', '?')}"

print(process_message({"role": "user", "content": "What is RAG?"}))
print(process_message({"role": "tool", "name": "search", "content": "results..."}))
```

**Gotcha:** `match`/`case` are *soft keywords* — they're only reserved inside a match statement. You can still have variables named `match` or `case` elsewhere in your code (though you probably shouldn't for readability).

---

## `case`

**Syntax:** `case pattern:` (a branch inside a `match` statement — Python 3.10+)

**When to use:** Define individual patterns within a `match` block — each `case` describes a structure to match against and optionally binds variables from it.

**Mental model:** A stencil — each `case` is a different stencil laid over the data. If the data fits through the holes (matches the pattern), the code under that case runs and the matched pieces are captured as variables.

```python
def parse_llm_finish_reason(reason: str | None) -> str:
    """Interpret LLM finish reasons with pattern matching."""
    match reason:
        case "stop":
            return "Complete response"
        case "length":
            return "Truncated — increase max_tokens"
        case "content_filter":
            return "Blocked by safety filter"
        case "tool_calls":
            return "Model wants to call a tool"
        case None:
            return "Still streaming..."
        case _:
            return f"Unknown finish reason: {reason}"

print(parse_llm_finish_reason("stop"))           # Complete response
print(parse_llm_finish_reason("length"))          # Truncated
print(parse_llm_finish_reason(None))              # Still streaming...
print(parse_llm_finish_reason("new_reason"))      # Unknown finish reason

# Guards in case patterns — add conditions beyond structure
def classify_score(score: float) -> str:
    match score:
        case x if x >= 0.9:
            return "excellent"
        case x if x >= 0.7:
            return "good"
        case x if x >= 0.5:
            return "fair"
        case _:
            return "poor"

scores = [0.95, 0.75, 0.55, 0.3]
for s in scores:
    print(f"{s} -> {classify_score(s)}")
```

**Gotcha:** `case _:` is the wildcard pattern (like `default` in other languages) — it matches anything and should always be last. Without it, a `match` block silently does nothing if no pattern matches, which can hide bugs.
