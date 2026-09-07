# 07 — Classes & Scope

Object-oriented keywords and scope management — how to define structured types, type aliases, and control variable visibility in AI service architectures.

---

## `class`

**Syntax:** `class Name(Base):` (define a class)

**When to use:** Encapsulate state and behavior — LLM client wrappers, agent implementations, tool registries, pipeline stages with configuration, custom exception types.

**Mental model:** A blueprint — `class` defines the shape and behavior of objects. Each instance built from the blueprint gets its own state (`self.x`) but shares the same methods. It's how you go from "a bag of functions" to "a thing that knows how to do things."

```python
from typing import Any

class LLMClient:
    """Minimal LLM client wrapper with conversation state."""
    def __init__(self, model: str = "claude-3", temperature: float = 0.7) -> None:
        self.model = model
        self.temperature = temperature
        self.history: list[dict[str, str]] = []
        self._call_count = 0

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        self._call_count += 1
        response = f"[{self.model}] Response #{self._call_count} to: {message[:30]}"
        self.history.append({"role": "assistant", "content": response})
        return response

    @property
    def stats(self) -> dict[str, Any]:
        return {"calls": self._call_count, "messages": len(self.history)}

client = LLMClient(model="claude-3.5", temperature=0.0)
print(client.chat("What is RAG?"))
print(client.chat("Show me code"))
print(f"Stats: {client.stats}")

# Inheritance — specialized clients
class StreamingClient(LLMClient):
    def stream(self, message: str):
        for word in self.chat(message).split():
            yield word

for token in StreamingClient().stream("Explain embeddings"):
    print(f"  token: {token}")
```

**Gotcha:** Mutable class attributes are shared across all instances — `class Foo: items = []` means every `Foo()` shares the same list. Always initialize mutable state in `__init__` with `self.items = []`.

---

## `type`

**Syntax:** `type Alias = SomeType` (type alias statement — Python 3.12+)

**When to use:** Create readable type aliases for complex types used across your AI codebase — message lists, tool call signatures, embedding vectors, config dictionaries.

**Mental model:** A name tag for a type — instead of repeating `list[dict[str, str | list[dict[str, Any]]]]` everywhere, you give it a short, descriptive name. The alias is fully transparent to the type checker.

```python
from typing import Any

# Clean aliases for complex types used throughout an AI codebase
type Message = dict[str, str]
type Conversation = list[Message]
type Embedding = list[float]
type ToolResult = dict[str, Any]
type ToolHandler = callable  # simplified

def format_conversation(convo: Conversation) -> str:
    """Using the alias makes the signature readable."""
    lines: list[str] = []
    for msg in convo:
        prefix = ">>" if msg["role"] == "user" else "<<"
        lines.append(f"{prefix} {msg['content'][:50]}")
    return "\n".join(lines)

def cosine_similarity(a: Embedding, b: Embedding) -> float:
    """Type alias documents what the list[float] represents."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x**2 for x in a) ** 0.5
    norm_b = sum(x**2 for x in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

convo: Conversation = [
    {"role": "user", "content": "What is RAG?"},
    {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation..."},
]
print(format_conversation(convo))

emb1: Embedding = [0.1, 0.2, 0.3, 0.4]
emb2: Embedding = [0.1, 0.3, 0.2, 0.5]
print(f"Similarity: {cosine_similarity(emb1, emb2):.3f}")
```

**Gotcha:** `type` as a statement is Python 3.12+ only. On older versions, use `TypeAlias` from `typing`: `Embedding: TypeAlias = list[float]`. Also, `type` is a *soft keyword* — it's only special at the start of a statement, so existing code using `type` as a variable name still works.

---

## `global`

**Syntax:** `global var_name` (declare that a variable in a function refers to the module-level name)

**When to use:** Rarely — module-level singletons like a shared LLM client, a global config, or a metrics counter. Almost always better replaced by a class, a module attribute, or dependency injection.

**Mental model:** A loudspeaker declaration — "I'm not creating a local variable, I'm talking about the one everyone can see." Without `global`, assigning to a name inside a function creates a new local variable that shadows the module-level one.

```python
from typing import Any

# Global config pattern (simple but use sparingly)
_config: dict[str, Any] = {"model": "claude-3", "temperature": 0.7}

def update_config(**overrides: Any) -> None:
    global _config
    _config = {**_config, **overrides}

def get_config() -> dict[str, Any]:
    return _config  # Reading doesn't need 'global'

print(f"Before: {get_config()}")
update_config(model="claude-3.5", temperature=0.0)
print(f"After:  {get_config()}")

# Global counter for tracking (metrics, debugging)
_total_llm_calls = 0

def call_llm(prompt: str) -> str:
    global _total_llm_calls
    _total_llm_calls += 1
    return f"Response #{_total_llm_calls}"

call_llm("Query 1")
call_llm("Query 2")
print(f"Total LLM calls: {_total_llm_calls}")
```

**Gotcha:** `global` makes code harder to test and reason about — any function can mutate shared state at any time. In production AI services, prefer dependency injection (pass the config as a parameter) or a class instance. Reserve `global` for genuinely module-level singletons with simple initialization.

---

## `nonlocal`

**Syntax:** `nonlocal var_name` (refer to a variable in the nearest enclosing function scope)

**When to use:** Closures that need to mutate state — callback counters, retry trackers, memoization state in nested functions, factory functions that return stateful callables.

**Mental model:** A "borrow from my parent" note — `nonlocal` says "I don't want the module-level variable, I want the one from the function that created me." It's `global` but scoped to the enclosing function instead of the module.

```python
from typing import Any, Callable

def make_rate_limiter(max_calls: int, period_name: str = "window") -> Callable[[], bool]:
    """Create a closure-based rate limiter."""
    calls_made = 0

    def try_call() -> bool:
        nonlocal calls_made
        if calls_made >= max_calls:
            print(f"  Rate limit hit: {calls_made}/{max_calls} in {period_name}")
            return False
        calls_made += 1
        print(f"  Call {calls_made}/{max_calls} allowed")
        return True

    return try_call

limiter = make_rate_limiter(3, "minute")
for i in range(5):
    limiter()

# nonlocal in a retry wrapper
def make_retry_tracker() -> Callable[[str], dict[str, Any]]:
    """Track retries across calls with closure state."""
    attempt = 0
    errors: list[str] = []

    def track(status: str) -> dict[str, Any]:
        nonlocal attempt
        attempt += 1
        if status == "error":
            errors.append(f"attempt {attempt}")
        return {"attempt": attempt, "errors": errors.copy(), "last": status}

    return track

tracker = make_retry_tracker()
print(tracker("error"))    # attempt 1, error
print(tracker("error"))    # attempt 2, errors: [1, 2]
print(tracker("success"))  # attempt 3, success
```

**Gotcha:** Without `nonlocal`, assigning to `calls_made` inside the nested function creates a new local variable — the closure's state never updates. You get an `UnboundLocalError` if you try to read it before the assignment. `nonlocal` is required specifically for *rebinding* (assignment); you can *mutate* a mutable object (like appending to a list) without it.

---

## `del`

**Syntax:** `del name` / `del obj[key]` / `del obj.attr` (delete a reference, item, or attribute)

**When to use:** Free large objects from memory — drop embedding matrices after use, remove sensitive data from dicts before logging, clean up cache entries, manage GPU memory.

**Mental model:** Tearing off a name tag — `del` removes the reference (the name tag), not necessarily the object. The object only gets garbage-collected when all references to it are gone. For containers, `del d[key]` removes the item itself.

```python
import sys
from typing import Any

# Free large data structures after processing
def process_embeddings(texts: list[str]) -> list[float]:
    """Compute embeddings and free the intermediate matrix."""
    # Simulate a large embedding matrix
    embedding_matrix = [[0.1 * i for i in range(768)] for _ in texts]
    print(f"Matrix memory: ~{sys.getsizeof(embedding_matrix):,} bytes")

    # Extract just the averages we need
    averages = [sum(row) / len(row) for row in embedding_matrix]

    # Free the large matrix — don't wait for GC
    del embedding_matrix
    return averages

scores = process_embeddings(["text1", "text2", "text3"])
print(f"Averages: {[f'{s:.2f}' for s in scores]}")

# del to remove sensitive data before logging
def sanitize_for_logging(request: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive fields before logging an API request."""
    safe = request.copy()
    for key in ["api_key", "auth_token", "password"]:
        if key in safe:
            del safe[key]
    return safe

req = {"model": "claude-3", "prompt": "Hello", "api_key": "sk-secret-123"}
print(f"Logged: {sanitize_for_logging(req)}")
print(f"Original intact: {'api_key' in req}")  # True — original untouched

# del to manage dict-based caches
cache: dict[str, str] = {"q1": "answer1", "q2": "answer2", "q3": "answer3"}
if len(cache) > 2:
    oldest = next(iter(cache))
    del cache[oldest]
    print(f"Evicted {oldest}, remaining: {list(cache.keys())}")
```

**Gotcha:** `del` only removes the reference, not the object — if another variable points to the same object, it stays in memory. Also, `del` on a variable makes it undefined; accessing it afterward raises `NameError`. Don't use `del` as a substitute for proper scoping or garbage collection.
