# 02 — Boolean Logic

Short-circuit boolean operators — the building blocks of guard clauses, fallback chains, and conditional logic in every AI pipeline.

---

## `and`

**Syntax:** `a and b` (returns `a` if falsy, else `b`)

**When to use:** Guard clauses that chain multiple conditions — validate inputs before calling an LLM, check that all prerequisites are met before running a pipeline step.

**Mental model:** A security checkpoint with two guards — you only get through if BOTH let you pass. But Python is lazy: if the first guard rejects you, the second never even looks at you (short-circuit evaluation).

```python
from typing import Any

def should_call_llm(request: dict[str, Any]) -> bool:
    """Gate LLM calls with chained validation."""
    return bool(
        request.get("prompt")
        and len(request["prompt"]) < 100_000
        and request.get("model") in {"claude-3", "gpt-4"}
        and request.get("tokens_remaining", 0) > 0
    )

# Short-circuit: stops at first falsy condition
print(should_call_llm({"prompt": "Hello", "model": "claude-3", "tokens_remaining": 500}))  # True
print(should_call_llm({"prompt": "", "model": "claude-3"}))  # False — empty prompt
print(should_call_llm({"prompt": "Hi", "model": "llama"}))   # False — unsupported model

# and returns the actual value, not just True/False
config = {"system_prompt": "You are helpful."}
system = config.get("system_prompt") and config["system_prompt"].strip()
print(f"System: {system!r}")  # 'You are helpful.'

empty_config: dict[str, str] = {}
system = empty_config.get("system_prompt") and empty_config["system_prompt"].strip()
print(f"System: {system!r}")  # None (short-circuited, .strip() never called)
```

**Gotcha:** `and` returns the actual operand, not `True`/`False`. `0 and "hello"` returns `0`, not `False`. This is useful for chaining but can surprise you if you expect a strict boolean.

---

## `or`

**Syntax:** `a or b` (returns `a` if truthy, else `b`)

**When to use:** Fallback chains — provide default values, pick the first available result, set backup models or configurations.

**Mental model:** A vending machine with a backup slot — it gives you the first item that's actually there. If slot A is empty, it tries slot B, then slot C, until something comes out.

```python
import os

def get_api_key() -> str:
    """Try multiple sources for the API key, fall back in order."""
    return (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("AI_API_KEY")
        or os.environ.get("DEFAULT_API_KEY")
        or "sk-test-key-for-development"
    )

def get_model(user_pref: str | None, team_default: str | None) -> str:
    """Resolve model with fallback chain."""
    return user_pref or team_default or "claude-3"

# or picks the first truthy value
print(get_model("gpt-4", "claude-3"))    # gpt-4 (user pref wins)
print(get_model(None, "claude-3"))        # claude-3 (team default)
print(get_model(None, None))              # claude-3 (hardcoded fallback)
print(get_model("", "claude-3"))          # claude-3 (empty string is falsy)

# Practical: default system prompt
user_system = ""
system = user_system or "You are a helpful AI assistant."
print(f"Using: {system}")
```

**Gotcha:** `or` treats `0`, `""`, `[]`, and `0.0` as falsy — so `temperature or 0.7` returns `0.7` when temperature is `0`, which is probably not what you want. Use `if temperature is not None` for numeric defaults where zero is valid.

---

## `not`

**Syntax:** `not x` (boolean negation)

**When to use:** Invert conditions — check for empty responses, missing keys, failed validations, or negated feature flags.

**Mental model:** A light switch flipper — it turns True to False and False to True. Unlike `and`/`or`, it always returns a strict `bool`.

```python
from typing import Any

def needs_retry(response: dict[str, Any]) -> bool:
    """Check if an LLM response needs retrying."""
    if not response:
        return True
    if not response.get("content"):
        return True
    if not response.get("finish_reason") == "stop":
        return True
    return False

# not with membership checks
BLOCKED_TOPICS = {"politics", "violence", "illegal"}

def is_safe_query(query: str) -> bool:
    """Simple content filter."""
    words = set(query.lower().split())
    return not words & BLOCKED_TOPICS  # True if no overlap

print(is_safe_query("Explain RAG architecture"))       # True
print(is_safe_query("Explain politics in detail"))      # False

# not in guard clauses
def process_batch(items: list[str]) -> list[str]:
    if not items:
        return []
    # Only reached if items is non-empty
    return [item.upper() for item in items]

print(process_batch([]))                # []
print(process_batch(["hello", "world"])) # ['HELLO', 'WORLD']
```

**Gotcha:** `not` has lower precedence than comparison operators: `not x == y` is parsed as `not (x == y)`, not `(not x) == y`. Use parentheses when combining `not` with comparisons to make intent clear.
