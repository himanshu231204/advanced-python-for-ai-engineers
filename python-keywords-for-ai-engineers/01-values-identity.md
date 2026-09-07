# 01 — Values & Identity

Python's built-in singleton values and the two keywords that test identity and membership — the foundation of every conditional check in AI pipelines.

---

## `True`

**Syntax:** `True` (boolean literal, no parentheses)

**When to use:** Flags, feature toggles, and explicit boolean state in agent configs and LLM call parameters.

**Mental model:** The green light — an unconditional "yes" that Python recognises as the canonical truthy value. It's also the integer `1` under the hood (`True + True == 2`).

```python
from dataclasses import dataclass

@dataclass
class LLMCallConfig:
    """Configuration for an LLM API call."""
    stream: bool = True
    include_usage: bool = True
    store_conversation: bool = False
    temperature: float = 0.7

config = LLMCallConfig()

if config.stream:
    print("Streaming response token by token...")
if config.include_usage:
    print("Token usage will be tracked")

# Boolean arithmetic for quick metrics
results = [True, False, True, True, False]
success_rate = sum(results) / len(results)
print(f"Tool call success rate: {success_rate:.0%}")  # 60%
```

**Gotcha:** `True` is a singleton — use `is True` only when you specifically need to distinguish `True` from other truthy values (like `1` or `"yes"`). In most cases, plain `if value:` is clearer and more Pythonic.

---

## `False`

**Syntax:** `False` (boolean literal)

**When to use:** Default states, disabled features, and sentinel returns when a tool call or validation fails.

**Mental model:** The red light — Python's canonical falsy value. Like `True`, it doubles as an integer (`False == 0`).

```python
from typing import Any

def validate_tool_output(output: dict[str, Any]) -> bool:
    """Validate that a tool call returned usable results."""
    if not output:
        return False
    if "error" in output:
        return False
    if not output.get("result"):
        return False
    return True

# Agent loop uses the boolean return to decide next step
tool_output = {"result": "Paris is the capital of France", "tokens": 12}
if validate_tool_output(tool_output):
    print(f"Valid: {tool_output['result']}")
else:
    print("Tool call failed — retrying with different parameters")

empty_output: dict[str, Any] = {}
print(f"Empty output valid: {validate_tool_output(empty_output)}")  # False
```

**Gotcha:** Don't compare with `== False` — use `not value` instead. The only exception is when `None` and `False` must be distinguished: `if value is False:` (rare in practice).

---

## `None`

**Syntax:** `None` (singleton literal)

**When to use:** Represent "no value" — missing API responses, optional parameters, unset agent state, sentinel for "not yet computed."

**Mental model:** An empty parking spot — the spot exists, but nothing is parked there. It's different from `0`, `""`, or `[]`, which are "something that happens to be empty."

```python
from typing import Any

class AgentMemory:
    """Simple agent memory with None as 'not found' sentinel."""
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._store.get(key, None)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

memory = AgentMemory()

# None signals "never computed" vs "" which means "computed but empty"
cached = memory.get("last_response")
if cached is None:
    print("Cache miss — calling LLM")
    memory.set("last_response", "RAG combines retrieval with generation...")
else:
    print(f"Cache hit: {cached[:50]}")

# Optional parameters with None defaults
def call_llm(prompt: str, system: str | None = None) -> str:
    parts = []
    if system is not None:
        parts.append(f"System: {system}")
    parts.append(f"User: {prompt}")
    return " | ".join(parts)

print(call_llm("What is RAG?"))
print(call_llm("What is RAG?", system="You are a helpful AI tutor."))
```

**Gotcha:** Always use `is None` / `is not None`, never `== None`. `None` is a singleton — identity check (`is`) is faster and avoids bugs with objects that override `__eq__`.

---

## `is`

**Syntax:** `a is b` (identity comparison)

**When to use:** Check if two variables point to the exact same object — sentinel checks (`is None`), singleton comparisons, cache identity verification.

**Mental model:** Checking ID cards — `==` asks "do you look the same?", while `is` asks "are you literally the same person?" Two identical twins are `==` but not `is`.

```python
from typing import Any

_MISSING = object()  # Unique sentinel — not None, not False, not 0

def get_config(overrides: dict[str, Any], key: str, default: Any = _MISSING) -> Any:
    """Get config with a sentinel that distinguishes 'not provided' from None."""
    value = overrides.get(key, _MISSING)
    if value is _MISSING:
        if default is _MISSING:
            raise KeyError(f"Required config key: {key}")
        return default
    return value

overrides = {"temperature": 0.9, "max_tokens": None}

temp = get_config(overrides, "temperature", default=0.7)
print(f"Temperature: {temp}")  # 0.9 (override wins)

# None is a valid override — sentinel pattern distinguishes it from "missing"
max_tok = get_config(overrides, "max_tokens", default=4096)
print(f"Max tokens: {max_tok}")  # None (explicitly set to None)

model = get_config(overrides, "model", default="claude-3")
print(f"Model: {model}")  # claude-3 (default, key not in overrides)
```

**Gotcha:** Never use `is` to compare integers, strings, or other immutable values — CPython interns small integers (-5 to 256) and some strings, so `a is b` may work by accident in tests but fail in production with different values.

---

## `in`

**Syntax:** `item in container` (membership test)

**When to use:** Check membership in collections — allowed models, supported tools, keyword filtering, stop-word detection, permission checks.

**Mental model:** The guest list — `in` checks whether a name appears on the list. Works with lists, sets, dicts, strings, and any object with `__contains__`.

```python
SUPPORTED_MODELS = {"claude-3", "claude-3.5", "gpt-4", "gpt-4o", "gemini-pro"}
STOP_WORDS = frozenset({"the", "a", "an", "is", "in", "on", "at", "to", "for"})

def validate_model(model: str) -> bool:
    """Check if a model is in our supported set."""
    return model in SUPPORTED_MODELS

def filter_tokens(tokens: list[str]) -> list[str]:
    """Remove stop words from tokenized text before embedding."""
    return [t for t in tokens if t.lower() not in STOP_WORDS]

def check_tool_permissions(tool: str, allowed: set[str]) -> bool:
    """Gate agent tool access."""
    if tool not in allowed:
        print(f"Tool '{tool}' not in allowed set: {allowed}")
        return False
    return True

print(validate_model("claude-3.5"))  # True
print(validate_model("llama-70b"))   # False

tokens = ["What", "is", "the", "capital", "of", "France"]
filtered = filter_tokens(tokens)
print(f"Filtered: {filtered}")  # ['What', 'capital', 'France']

allowed_tools = {"web_search", "calculator", "code_exec"}
check_tool_permissions("web_search", allowed_tools)  # True
check_tool_permissions("file_delete", allowed_tools)  # not in allowed set
```

**Gotcha:** `in` on a `list` is O(n) — for hot-path membership checks (per-token filtering, per-request validation), use a `set` or `frozenset` for O(1) lookups. This matters when processing thousands of tokens or requests.
