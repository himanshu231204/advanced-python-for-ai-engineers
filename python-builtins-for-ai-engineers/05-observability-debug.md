# 05 — Observability & Debug

See what your AI system is actually doing — structured logging, error tracing, runtime inspection, and performance profiling.

---

## `logging`

**Import:** `import logging`

**When to use:** Structured, leveled output for every production AI service — track LLM calls, token usage, latencies, and errors without `print()` spam.

**Mental model:** A flight recorder for your application — it captures everything at configurable detail levels, and you can replay it after a crash without needing to reproduce the bug.

```python
import logging
import time

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("agent")

def log_llm_call(model: str, prompt_tokens: int, completion_tokens: int,
                 latency_ms: float) -> None:
    """Structured logging for LLM API observability."""
    logger.info(
        "LLM call completed",
        extra={
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": round(latency_ms, 1),
            "cost_usd": (prompt_tokens * 0.003 + completion_tokens * 0.015) / 1000,
        },
    )

start = time.perf_counter()
# ... LLM call happens here ...
elapsed = (time.perf_counter() - start) * 1000
log_llm_call("claude-3-opus", prompt_tokens=500, completion_tokens=200, latency_ms=elapsed)
```

**Gotcha:** `logging.basicConfig()` only works if called before any logger is used — if a library imports logging first, your config is silently ignored. Call it at the top of your entry point.

---

## `traceback`

**Import:** `import traceback`

**When to use:** Capture and store exception details from agent tool calls without crashing the main loop — essential for resilient multi-step agents.

**Mental model:** A crime scene photographer — it captures the full stack trace as a string so you can log it, send it, or store it, without re-raising the exception.

```python
import traceback

def safe_tool_execute(tool_name: str, tool_fn: callable, **kwargs: object) -> dict[str, str]:
    """Run an agent tool, capturing failures without crashing the loop."""
    try:
        result = tool_fn(**kwargs)
        return {"status": "ok", "result": str(result)}
    except Exception:
        tb = traceback.format_exc()
        return {
            "status": "error",
            "tool": tool_name,
            "traceback": tb,
            "summary": tb.strip().splitlines()[-1],
        }

# Agent loop stays alive even when individual tools fail
def bad_tool(**kwargs: object) -> None:
    raise ConnectionError("Vector DB unreachable")

result = safe_tool_execute("vector_search", bad_tool)
print(f"Tool failed: {result['summary']}")
# Tool failed: ConnectionError: Vector DB unreachable
```

**Gotcha:** `traceback.format_exc()` returns `"NoneType: None\n"` when called outside an exception handler — always use it inside an `except` block.

---

## `inspect`

**Import:** `import inspect`

**When to use:** Auto-generate tool schemas from function signatures, build dynamic function registries for agents, introspect callables at runtime.

**Mental model:** An X-ray machine for functions — it sees the parameter names, types, defaults, and docstrings without running the function.

```python
import inspect
from typing import Any, get_type_hints

def auto_tool_schema(fn: callable) -> dict[str, Any]:
    """Generate an LLM tool-use schema from a function's signature and docstring."""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)
    type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}

    properties: dict[str, dict[str, str]] = {}
    required: list[str] = []
    for name, param in sig.parameters.items():
        prop_type = type_map.get(hints.get(name, str), "string")
        properties[name] = {"type": prop_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "name": fn.__name__,
        "description": (inspect.getdoc(fn) or "").split("\n")[0],
        "parameters": {"type": "object", "properties": properties, "required": required},
    }

def web_search(query: str, max_results: int = 5) -> list[str]:
    """Search the web for relevant documents."""
    return [f"result_{i}" for i in range(max_results)]

schema = auto_tool_schema(web_search)
print(schema["name"])  # web_search
print(schema["parameters"]["required"])  # ['query']
```

**Gotcha:** `inspect.signature()` doesn't resolve `from __future__ import annotations` string annotations. Use `get_type_hints()` for resolved types, but catch `NameError` for forward references.

---

## `warnings`

**Import:** `import warnings`

**When to use:** Deprecation notices in your tool/SDK, surfacing non-fatal issues (rate limit approaching, model fallback), filtering noisy library warnings.

**Mental model:** A yellow traffic light — it doesn't stop execution, but it signals "pay attention, something isn't ideal" to developers or operators.

```python
import warnings

def call_model(model: str, prompt: str) -> str:
    """Route to the correct model, warning on deprecated names."""
    deprecated = {"gpt-4": "gpt-4o", "claude-2": "claude-3-haiku-20240307"}
    if model in deprecated:
        new = deprecated[model]
        warnings.warn(
            f"Model '{model}' is deprecated, use '{new}' instead. "
            f"This alias will be removed in v2.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        model = new
    return f"[{model}] Response to: {prompt}"

# In tests or CI, turn warnings into errors to catch deprecations early:
# warnings.filterwarnings("error", category=DeprecationWarning)

# In production, suppress noisy third-party warnings:
# warnings.filterwarnings("ignore", module="urllib3")
```

**Gotcha:** Python deduplicates warnings by default — the same warning from the same location shows only once per process. Use `warnings.simplefilter("always")` in tests if you need to see repeats.

---

## `cProfile`

**Import:** `import cProfile`

**When to use:** Find bottlenecks in your agent pipeline — is it the embedding computation, the JSON serialization, or the network call that's slow?

**Mental model:** A stopwatch on every function call — it records exactly how many times each function ran and how much time it consumed, so you optimize the right thing.

```python
import cProfile
import pstats
import io

def profile_agent_step(fn: callable, *args: object) -> str:
    """Profile a function and return the top 10 bottlenecks as a string."""
    profiler = cProfile.Profile()
    profiler.enable()
    fn(*args)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(10)
    return stream.getvalue()

def expensive_pipeline() -> None:
    """Simulated agent pipeline with multiple stages."""
    data = [str(i) for i in range(100_000)]       # tokenization
    encoded = [d.encode("utf-8") for d in data]    # encoding
    joined = b"\n".join(encoded)                    # serialization

report = profile_agent_step(expensive_pipeline)
print(report[:500])
```

**Gotcha:** `cProfile` measures wall time by default and includes I/O waits. For CPU-only timing, use `cProfile` on sync code and complement with `time.perf_counter()` for async latency tracking.
