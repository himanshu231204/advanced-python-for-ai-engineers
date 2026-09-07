# 08 — Error Handling & Resources

Exception handling, resource management, and the import system — the infrastructure keywords that make AI services reliable, safe, and modular.

---

## `try`

**Syntax:** `try:` (begin a block that might raise an exception)

**When to use:** Wrap any operation that can fail at runtime — LLM API calls, JSON parsing of model output, file I/O, database queries, HTTP requests.

**Mental model:** A safety net under a tightrope — you try the risky operation, and if you fall (exception), the net (`except`) catches you instead of crashing the whole show. Always pair with `except`.

```python
import json
from typing import Any

def parse_llm_json(raw: str) -> dict[str, Any]:
    """Safely parse JSON from LLM output — models don't always produce valid JSON."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            try:
                return json.loads(raw[start:end].strip())
            except json.JSONDecodeError:
                return {"raw": raw, "error": "Failed to parse JSON"}
        return {"raw": raw, "error": "Not valid JSON"}

# LLM sometimes wraps JSON in markdown
clean = parse_llm_json('{"tool": "search", "query": "RAG"}')
print(f"Clean: {clean}")

wrapped = parse_llm_json('```json\n{"tool": "search"}\n```')
print(f"Wrapped: {wrapped}")

broken = parse_llm_json("I think the answer is 42")
print(f"Broken: {broken}")
```

**Gotcha:** Never use bare `try: ... except:` (catches everything, including `KeyboardInterrupt` and `SystemExit`). Always catch specific exceptions. If you must catch broadly, use `except Exception:` at minimum — it skips the system-exit signals.

---

## `except`

**Syntax:** `except ExceptionType as e:` (handle a specific exception)

**When to use:** Handle specific failure modes — API rate limits, network timeouts, validation errors, missing keys in LLM output, database connection failures.

**Mental model:** A specialist catcher — each `except` block is trained to catch one type of problem. Like a hospital ER with different specialists: the broken-bone doctor handles fractures, the allergy doctor handles reactions. Each one knows what to do for their specific case.

```python
import json
from typing import Any

class RateLimitError(Exception):
    """Custom exception for rate limit hits."""
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s")

def call_api(endpoint: str) -> dict[str, Any]:
    """Simulate an API call with different failure modes."""
    if "rate" in endpoint:
        raise RateLimitError(retry_after=2.0)
    if "bad" in endpoint:
        raise ValueError("Invalid request")
    return {"status": "ok"}

def resilient_call(endpoint: str) -> dict[str, Any]:
    """Handle each failure mode differently."""
    try:
        return call_api(endpoint)
    except RateLimitError as e:
        print(f"  Rate limited — would retry in {e.retry_after}s")
        return {"status": "rate_limited", "retry_after": e.retry_after}
    except ValueError as e:
        print(f"  Bad request: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"  Unexpected error: {type(e).__name__}: {e}")
        return {"status": "error", "message": "Unknown failure"}

print(resilient_call("/api/chat"))
print(resilient_call("/api/rate-limit"))
print(resilient_call("/api/bad-request"))

# Multiple exceptions in one handler (Python 3.11+ ExceptionGroup also available)
def parse_config(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"  Config parse error ({type(e).__name__}): {e}")
        return {}

parse_config("not json")
```

**Gotcha:** Order matters — `except` blocks are checked top to bottom, and the first match wins. Putting `except Exception` before `except ValueError` means `ValueError` is never reached. Always order from most specific to most general.

---

## `finally`

**Syntax:** `finally:` (code that runs no matter what — exception or not)

**When to use:** Guaranteed cleanup — close database connections, release locks, flush logs, stop timers, clean up temporary files, regardless of whether the operation succeeded.

**Mental model:** The closing act — no matter what happened during the show (success, error, even if someone pulled the fire alarm), the closing act always performs. It runs after `try` and `except`, guaranteed.

```python
import time
from typing import Any

class Timer:
    """Simple timer for measuring LLM call latency."""
    def __init__(self, label: str) -> None:
        self.label = label
        self.start = 0.0

    def begin(self) -> None:
        self.start = time.perf_counter()

    def end(self) -> None:
        elapsed = time.perf_counter() - self.start
        print(f"  [{self.label}] {elapsed:.3f}s")

def call_with_metrics(query: str) -> str:
    """Track latency regardless of success or failure."""
    timer = Timer("llm_call")
    timer.begin()
    try:
        if "error" in query:
            raise RuntimeError("Simulated API failure")
        return f"Response to: {query}"
    except RuntimeError as e:
        print(f"  Error: {e}")
        return f"Fallback response for: {query}"
    finally:
        timer.end()  # Always records timing, even on error

print(call_with_metrics("What is RAG?"))
print(call_with_metrics("trigger error please"))

# finally for resource cleanup
def process_with_tempfile(data: str) -> str:
    """Write to temp, process, clean up no matter what."""
    import tempfile, os
    path = ""
    try:
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.write(fd, data.encode())
        os.close(fd)
        # Process the file
        return f"Processed {len(data)} bytes from {path}"
    finally:
        if path and os.path.exists(path):
            os.unlink(path)
            print(f"  Cleaned up: {path}")

print(process_with_tempfile("embedding data..."))
```

**Gotcha:** `finally` runs even if you `return` from inside `try` or `except` — but if `finally` itself has a `return`, it silently overrides the original return value. Never put `return` in a `finally` block.

---

## `raise`

**Syntax:** `raise ExceptionType("message")` / `raise` (re-raise current) / `raise X from Y` (chain)

**When to use:** Signal errors explicitly — validation failures, unsupported operations, re-raise after logging, wrap low-level exceptions in domain-specific ones.

**Mental model:** Pulling the fire alarm — `raise` immediately stops normal execution and sends an emergency signal (the exception) up the call stack. Someone above must handle it, or the program crashes.

```python
from typing import Any

class TokenBudgetExceeded(Exception):
    """Raised when an agent exceeds its token budget."""
    def __init__(self, used: int, limit: int) -> None:
        self.used = used
        self.limit = limit
        super().__init__(f"Token budget exceeded: {used}/{limit}")

def check_budget(used: int, limit: int) -> None:
    if used > limit:
        raise TokenBudgetExceeded(used, limit)

# raise from — exception chaining preserves the root cause
def load_model_config(path: str) -> dict[str, Any]:
    import json
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(f"Model config not found: {path}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {path}") from e

# bare raise — re-raise after logging
def safe_embed(text: str) -> list[float]:
    try:
        if not text.strip():
            raise ValueError("Cannot embed empty text")
        return [0.1, 0.2, 0.3]
    except ValueError:
        print(f"  Logging: embed failed for text={text!r}")
        raise  # Re-raises the same ValueError with original traceback

try:
    check_budget(used=15000, limit=10000)
except TokenBudgetExceeded as e:
    print(f"Caught: {e} (used={e.used}, limit={e.limit})")

try:
    safe_embed("")
except ValueError as e:
    print(f"Caught after logging: {e}")
```

**Gotcha:** Use `raise X from Y` (not bare `raise X`) when wrapping exceptions — it preserves the original traceback in `__cause__`, making debugging much easier. Without `from`, the original exception appears as "during handling of the above exception" instead of a clean chain.

---

## `assert`

**Syntax:** `assert condition, "message"` (debug-mode invariant check)

**When to use:** Development-time checks — verify invariants in pipelines, confirm expected shapes/types during development, self-documenting assumptions in code.

**Mental model:** A confidence check — "I'm so sure this is true that if it's not, something is fundamentally broken and I want to crash loudly right now so I can fix it." It's a developer tool, not a runtime validation tool.

```python
from typing import Any

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks for RAG."""
    assert chunk_size > 0, f"chunk_size must be positive, got {chunk_size}"
    assert overlap < chunk_size, f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
    assert isinstance(text, str), f"Expected str, got {type(text)}"

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

chunks = chunk_text("A" * 100, chunk_size=30, overlap=10)
print(f"Chunks: {len(chunks)}, each ~30 chars with 10 char overlap")

# Assert to document pipeline invariants
def merge_results(
    llm_results: list[dict[str, Any]],
    tool_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assert len(llm_results) == len(tool_results), (
        f"Result count mismatch: {len(llm_results)} LLM vs {len(tool_results)} tool"
    )
    return [
        {**llm, "tool_output": tool.get("output")}
        for llm, tool in zip(llm_results, tool_results)
    ]

merged = merge_results(
    [{"response": "A"}, {"response": "B"}],
    [{"output": "1"}, {"output": "2"}],
)
print(f"Merged: {merged}")
```

**Gotcha:** `assert` statements are removed when Python runs with optimization (`python -O`). Never use `assert` for input validation, permission checks, or anything that must run in production. Use `if ... raise ValueError(...)` for real runtime validation.

---

## `with`

**Syntax:** `with expression as var:` (context manager — guaranteed setup and teardown)

**When to use:** Manage resources that need cleanup — file handles, database connections, HTTP sessions, locks, temporary directories, timing contexts.

**Mental model:** A responsible borrower — `with` borrows a resource, uses it, and guarantees it's returned (cleaned up) when done, even if an error occurs. It's `try`/`finally` in a clean, reusable package.

```python
import json
import time
from contextlib import contextmanager
from typing import Any, Generator

@contextmanager
def llm_session(model: str) -> Generator[dict[str, Any], None, None]:
    """Context manager for an LLM session with setup/teardown."""
    session: dict[str, Any] = {
        "model": model,
        "start": time.perf_counter(),
        "calls": 0,
    }
    print(f"  Opening session: {model}")
    try:
        yield session
    finally:
        elapsed = time.perf_counter() - session["start"]
        print(f"  Closing session: {session['calls']} calls in {elapsed:.3f}s")

# with guarantees the session is closed even if an error occurs
with llm_session("claude-3") as sess:
    sess["calls"] += 1
    print(f"  Made {sess['calls']} call(s)")
    sess["calls"] += 1
    print(f"  Made {sess['calls']} call(s)")

# Multiple context managers in one with statement (Python 3.10+)
@contextmanager
def timer(label: str) -> Generator[None, None, None]:
    start = time.perf_counter()
    yield
    print(f"  [{label}] {time.perf_counter() - start:.4f}s")

# Nested resource management — all cleaned up in reverse order
with (
    llm_session("claude-3") as sess,
    timer("total"),
):
    sess["calls"] += 1
    print(f"  Working with session, call #{sess['calls']}")
```

**Gotcha:** `with` only guarantees `__exit__` (or the `finally` in a `@contextmanager`) is called — it doesn't swallow exceptions by default. The exception still propagates after cleanup unless the context manager explicitly suppresses it (like `contextlib.suppress`).

---

## `import`

**Syntax:** `import module` / `import module as alias` (load a module)

**When to use:** Every Python file — bring in stdlib, third-party libraries, and your own modules. Organize imports to make dependencies clear and enable lazy loading for heavy libraries.

**Mental model:** A library card — `import` goes to Python's library, finds the module by name, loads it, and gives you a reference. The module is loaded once and cached; subsequent imports reuse the same object.

```python
import json
import time
import importlib
from typing import Any

# Standard import patterns for AI engineering
import asyncio
import logging

# Lazy import — don't load heavy libraries until needed
def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Lazy-import numpy only when called — keeps startup fast."""
    try:
        np = importlib.import_module("numpy")
        # Would use np for real embedding math
        return [[0.1] * 768 for _ in texts]
    except ImportError:
        # Fallback without numpy
        return [[0.1] * 768 for _ in texts]

# Conditional imports — adapt to available libraries
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("Using uvloop for faster async")
except ImportError:
    print("Using default asyncio event loop")

# Dynamic import for plugin systems
def load_tool(tool_name: str) -> Any:
    """Dynamically import a tool module by name."""
    try:
        module = importlib.import_module(f"tools.{tool_name}")
        return getattr(module, "run", None)
    except (ImportError, AttributeError):
        return None
```

**Gotcha:** Circular imports (`a` imports `b`, `b` imports `a`) cause `ImportError` or partially initialized modules. Fix by moving the import inside the function that needs it, or restructure your modules to eliminate the cycle.

---

## `from`

**Syntax:** `from module import name` (import specific names from a module)

**When to use:** Import specific classes, functions, or constants — cleaner than using `module.name` everywhere, especially for frequently used names.

**Mental model:** Cherry-picking from a toolbox — instead of grabbing the entire toolbox (`import toolbox`), you reach in and pull out just the wrench and screwdriver you need (`from toolbox import wrench, screwdriver`).

```python
from typing import Any
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

@dataclass
class ToolCallMetrics:
    """Track tool usage metrics using cherry-picked imports."""
    calls: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, tool: str, success: bool) -> None:
        self.calls[tool] += 1
        if not success:
            self.errors[tool] += 1

    def summary(self) -> dict[str, Any]:
        return {
            tool: {
                "calls": count,
                "errors": self.errors[tool],
                "success_rate": f"{(count - self.errors[tool]) / count:.0%}",
            }
            for tool, count in self.calls.items()
        }

metrics = ToolCallMetrics()
metrics.record("search", True)
metrics.record("search", True)
metrics.record("search", False)
metrics.record("calculator", True)

for tool, stats in metrics.summary().items():
    print(f"  {tool}: {stats}")

# from with relative imports (inside packages)
# from .utils import chunk_text      # relative import within a package
# from ..config import settings      # parent package import
```

**Gotcha:** `from module import *` (star import) pollutes your namespace and makes it impossible to tell where names come from. Always import specific names. The one exception: `from typing import *` in type stubs (`.pyi` files), where it's conventional.

---

## `as`

**Syntax:** `import X as Y` / `except E as e` / `with X as var` (bind to an alias)

**When to use:** Alias long module names, capture exception objects for inspection, bind context manager results to variables. `as` serves three distinct roles but always means "give this thing a name."

**Mental model:** A nickname — `as` lets you call something by a shorter or more convenient name. The original name still exists; you just have an alias.

```python
import json as j
from collections import defaultdict as dd
from typing import Any

# as in imports — shorten verbose names
config = j.loads('{"model": "claude-3", "temperature": 0.7}')
print(f"Model: {config['model']}")

counts: dd[str, int] = dd(int)
for tool in ["search", "search", "calc", "search", "calc"]:
    counts[tool] += 1
print(f"Counts: {dict(counts)}")

# as in except — capture the exception for inspection
def safe_divide(a: float, b: float) -> float | None:
    try:
        return a / b
    except ZeroDivisionError as e:
        print(f"  Caught: {type(e).__name__}: {e}")
        return None

print(safe_divide(10, 3))  # 3.333...
print(safe_divide(10, 0))  # Caught: ZeroDivisionError

# as in with — bind the context manager's __enter__ result
from contextlib import contextmanager
from typing import Generator

@contextmanager
def db_connection(name: str) -> Generator[dict[str, Any], None, None]:
    conn: dict[str, Any] = {"name": name, "open": True}
    print(f"  Opened: {name}")
    try:
        yield conn  # This is what 'as' binds to
    finally:
        conn["open"] = False
        print(f"  Closed: {name}")

with db_connection("agent_memory") as conn:
    print(f"  Using: {conn['name']}, open={conn['open']}")

# All three uses in one block
import logging as log

try:
    with open("/tmp/test_as_keyword.txt", "w") as f:
        f.write("hello")
    log.info("Written")
except OSError as e:
    log.error(f"Failed: {e}")
```

**Gotcha:** In `except E as e`, the variable `e` is deleted after the except block exits (to break reference cycles with the traceback). If you need the exception object outside the block, assign it to another name: `saved = e` inside the except block.
