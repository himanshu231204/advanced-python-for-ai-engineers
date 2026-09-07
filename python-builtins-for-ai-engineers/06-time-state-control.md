# 06 — Time, State & Control

Timing, lifecycle hooks, clean enumerations, and memory-safe references — the operational backbone of long-running AI services.

---

## `time` / `datetime`

**Import:** `import time` / `from datetime import datetime, timezone, timedelta`

**When to use:** Measure LLM latencies, implement rate limiting, timestamp agent traces, calculate token-per-second throughput.

**Mental model:** `time` is a stopwatch (high-resolution intervals), `datetime` is a calendar (human-readable timestamps). Use the stopwatch for performance, the calendar for logs.

```python
import time
from datetime import datetime, timezone

class LatencyTracker:
    """Track per-call latency and throughput for an LLM endpoint."""
    def __init__(self) -> None:
        self.calls: list[dict[str, float | str]] = []

    def record(self, model: str, tokens: int, elapsed: float) -> None:
        self.calls.append({
            "model": model,
            "tokens": tokens,
            "latency_s": round(elapsed, 3),
            "tokens_per_sec": round(tokens / elapsed, 1) if elapsed > 0 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

tracker = LatencyTracker()
start = time.perf_counter()
time.sleep(0.05)  # simulates LLM call
elapsed = time.perf_counter() - start
tracker.record("claude-3-opus", tokens=350, elapsed=elapsed)
print(tracker.calls[-1])
```

**Gotcha:** `time.time()` is wall-clock and can jump backwards (NTP sync). Always use `time.perf_counter()` or `time.monotonic()` for measuring durations.

---

## `signal`

**Import:** `import signal`

**When to use:** Graceful shutdown of long-running agent processes — flush logs, save state, close connections before the container is killed.

**Mental model:** A fire alarm — when the OS sends a signal (SIGTERM, SIGINT), your handler runs cleanup code before the process exits, instead of dying mid-operation.

```python
import signal
import sys

class AgentProcess:
    """Agent that shuts down gracefully on SIGTERM/SIGINT."""
    def __init__(self) -> None:
        self.running = True
        self.pending_tasks: list[str] = []
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame: object) -> None:
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
        self._flush_state()
        sys.exit(0)

    def _flush_state(self) -> None:
        print(f"Flushing {len(self.pending_tasks)} pending tasks to disk")

    def run(self) -> None:
        print("Agent running (Ctrl+C to stop)")
        while self.running:
            self.pending_tasks.append("task")
            # ... agent loop work ...

# agent = AgentProcess()
# agent.run()
```

**Gotcha:** Signal handlers run in the main thread only — they silently do nothing in spawned threads or subprocesses. Also, only a limited set of operations is safe inside a handler.

---

## `atexit`

**Import:** `import atexit`

**When to use:** Register cleanup functions that run when your agent process exits — close DB connections, flush telemetry buffers, save checkpoints.

**Mental model:** A "close up shop" checklist that Python runs automatically when the interpreter exits, no matter how it exits (except `SIGKILL`).

```python
import atexit
import json
from pathlib import Path

class TelemetryBuffer:
    """Buffers telemetry events and flushes them on exit."""
    def __init__(self, path: str = "/tmp/agent_telemetry.jsonl") -> None:
        self.buffer: list[dict[str, object]] = []
        self.path = Path(path)
        atexit.register(self.flush)

    def record(self, event: dict[str, object]) -> None:
        self.buffer.append(event)

    def flush(self) -> None:
        if not self.buffer:
            return
        with open(self.path, "a") as f:
            for event in self.buffer:
                f.write(json.dumps(event) + "\n")
        print(f"Flushed {len(self.buffer)} telemetry events to {self.path}")
        self.buffer.clear()

telemetry = TelemetryBuffer()
telemetry.record({"event": "llm_call", "model": "claude-3", "tokens": 500})
telemetry.record({"event": "tool_call", "tool": "search", "latency_ms": 120})
# flush() runs automatically when the process exits
```

**Gotcha:** `atexit` handlers don't run if the process is killed with `SIGKILL` (`kill -9`) or if `os._exit()` is called. Combine with `signal` handlers for robust shutdown.

---

## `enum`

**Import:** `from enum import Enum, StrEnum`

**When to use:** Define fixed sets of valid values — agent states, model names, tool types, message roles — preventing typo bugs.

**Mental model:** A sealed envelope of allowed values — you can only pick from what's inside, and your IDE and type checker know the full list.

```python
from enum import StrEnum

class AgentState(StrEnum):
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALLING = "tool_calling"
    RESPONDING = "responding"
    ERROR = "error"

class ModelTier(StrEnum):
    FAST = "claude-3-haiku-20240307"
    BALANCED = "claude-3-sonnet-20240229"
    POWERFUL = "claude-3-opus-20240229"

def select_model(task_complexity: int) -> ModelTier:
    if task_complexity > 8:
        return ModelTier.POWERFUL
    elif task_complexity > 4:
        return ModelTier.BALANCED
    return ModelTier.FAST

model = select_model(9)
print(f"Selected: {model}")       # claude-3-opus-20240229
print(f"Is powerful: {model is ModelTier.POWERFUL}")  # True
```

**Gotcha:** `StrEnum` (Python 3.11+) values are actual strings and work in JSON directly. Plain `Enum` values are not — `json.dumps(MyEnum.VALUE)` raises `TypeError` without a custom serializer.

---

## `weakref`

**Import:** `import weakref`

**When to use:** Cache large objects (model instances, embedding matrices) without preventing garbage collection — avoid OOM in long-running services.

**Mental model:** A sticky note with someone's phone number — you can call them if they're still around, but the note doesn't prevent them from leaving. The object can be GC'd; your reference gracefully becomes `None`.

```python
import weakref

class ModelInstance:
    """Simulates a large loaded model."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.weights = bytearray(10_000_000)  # ~10MB

    def predict(self, text: str) -> str:
        return f"{self.name}: prediction for '{text[:20]}...'"

class ModelCache:
    """Cache that doesn't prevent GC of unused models."""
    def __init__(self) -> None:
        self._cache: dict[str, weakref.ref[ModelInstance]] = {}

    def get(self, name: str) -> ModelInstance | None:
        ref = self._cache.get(name)
        if ref is not None:
            instance = ref()
            if instance is not None:
                return instance
        return None

    def put(self, model: ModelInstance) -> None:
        self._cache[model.name] = weakref.ref(model)

cache = ModelCache()
m = ModelInstance("embedding-v2")
cache.put(m)
print(cache.get("embedding-v2") is not None)  # True
del m  # model can now be garbage collected
```

**Gotcha:** Not all Python objects support weak references — built-in types like `int`, `str`, `list`, `dict` don't. Wrap them in a class if you need weak refs.
