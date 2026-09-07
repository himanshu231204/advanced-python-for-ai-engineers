# 02 — Abstractions & Patterns

Building blocks for well-structured AI systems — interfaces, data containers, type safety, and composition.

---

## `abc`

**Import:** `from abc import ABC, abstractmethod`

**When to use:** Define a stable interface for swappable LLM providers, embedding backends, or vector stores.

**Mental model:** A blueprint contract — it forces every subclass to implement certain methods, so your agent code never calls a method that doesn't exist on a provider.

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs: object) -> str: ...

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: object):  # -> AsyncIterator[str]
        ...

class AnthropicProvider(LLMProvider):
    async def complete(self, prompt: str, **kwargs: object) -> str:
        return f"Claude says: {prompt[:50]}..."

    async def stream(self, prompt: str, **kwargs: object):
        for word in prompt.split():
            yield word

# This fails at instantiation, not at runtime deep in your pipeline:
# provider = LLMProvider()  # TypeError: Can't instantiate abstract class
```

**Gotcha:** Forgetting `@abstractmethod` on a method means the ABC won't enforce it — subclasses can silently skip the implementation and you discover the bug at runtime.

---

## `dataclasses`

**Import:** `from dataclasses import dataclass, field`

**When to use:** Lightweight structured data for agent state, tool results, config — when you don't need Pydantic's validation overhead.

**Mental model:** A labeled box with compartments — you declare what goes in each slot and Python auto-generates `__init__`, `__repr__`, `__eq__` for you.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentMessage:
    role: str
    content: str
    tool_calls: list[dict[str, str]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0

@dataclass
class ConversationState:
    messages: list[AgentMessage] = field(default_factory=list)
    total_tokens: int = 0

    def add(self, msg: AgentMessage) -> None:
        self.messages.append(msg)
        self.total_tokens += msg.token_count

state = ConversationState()
state.add(AgentMessage(role="user", content="Explain RAG", token_count=3))
state.add(AgentMessage(role="assistant", content="RAG is...", token_count=150))
print(f"Messages: {len(state.messages)}, Tokens: {state.total_tokens}")
```

**Gotcha:** Mutable default arguments bite hard — `tool_calls: list = []` shares one list across all instances. Always use `field(default_factory=list)`.

---

## `typing`

**Import:** `from typing import TypeVar, Protocol, TypeAlias`

**When to use:** Make agent/tool/pipeline interfaces self-documenting and catch integration bugs before runtime.

**Mental model:** Type annotations are guardrails on a highway — they don't slow you down, but they keep you from drifting into the wrong lane at 2 AM.

```python
from typing import Protocol, TypeAlias, Any
from collections.abc import AsyncIterator

# Type aliases keep signatures readable
Message: TypeAlias = dict[str, str]
Embedding: TypeAlias = list[float]
ToolResult: TypeAlias = dict[str, Any]

class Tool(Protocol):
    """Any object with this shape works as a tool — no inheritance needed."""
    name: str
    async def execute(self, **kwargs: Any) -> ToolResult: ...

class SearchTool:
    name: str = "web_search"
    async def execute(self, **kwargs: Any) -> ToolResult:
        return {"results": ["doc1", "doc2"]}

async def run_tool(tool: Tool, **kwargs: Any) -> ToolResult:
    print(f"Running tool: {tool.name}")
    return await tool.execute(**kwargs)

# SearchTool satisfies Tool protocol — no inheritance required
```

**Gotcha:** `dict` and `list` are covariant in type checkers but mutable at runtime. Use `Mapping` and `Sequence` in function signatures when you don't need mutation.

---

## `functools`

**Import:** `from functools import lru_cache, wraps, partial, reduce`

**When to use:** Cache expensive computations (tokenizer loading, config parsing), build decorator stacks for agents, create pre-configured callables.

**Mental model:** A Swiss Army knife for functions — it wraps, caches, composes, and curries them without rewriting the originals.

```python
import functools
import time
from typing import Any, Callable

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator: retry on exception with exponential backoff."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator

@functools.lru_cache(maxsize=4)
def load_tokenizer(model_name: str) -> str:
    """Expensive operation — only runs once per model_name."""
    print(f"Loading tokenizer for {model_name}...")
    return f"tokenizer:{model_name}"

# First call loads, second call is instant (cached)
tok1 = load_tokenizer("claude-3")
tok2 = load_tokenizer("claude-3")  # cache hit
```

**Gotcha:** `lru_cache` holds strong references to all arguments — caching with large objects as keys causes memory leaks. Use hashable, small keys only.

---

## `contextlib`

**Import:** `from contextlib import asynccontextmanager, contextmanager, suppress`

**When to use:** Manage lifecycle of LLM clients, database connections, temporary resources — ensure cleanup even on exceptions.

**Mental model:** A bouncer who checks you in AND checks you out — no matter what happens inside (even an exception), the cleanup code always runs.

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any

class FakeAsyncClient:
    async def close(self) -> None:
        print("Client closed")
    async def complete(self, prompt: str) -> str:
        return f"Response to: {prompt}"

@asynccontextmanager
async def llm_session(api_key: str) -> AsyncIterator[FakeAsyncClient]:
    """Guarantees the client is closed even if the agent loop crashes."""
    client = FakeAsyncClient()
    print(f"Session opened with key {api_key[:4]}...")
    try:
        yield client
    finally:
        await client.close()

# Usage in an agent:
# async with llm_session("sk-abc123") as client:
#     response = await client.complete("Hello")
#     print(response)
```

**Gotcha:** `@contextmanager` generators must yield exactly once. A missing `yield` or yielding in a conditional branch makes the context manager unusable.
