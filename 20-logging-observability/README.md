# 20 — Logging & Observability

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

You can't debug an agent you can't see. Structured logging and tracing concepts are what
make multi-step AI pipelines debuggable in production -- when a request touches a retriever,
an LLM call, and a response formatter, you need to reconstruct exactly what happened, in what
order, and how long each step took.

---

## 1. What is it?

Python's `logging` module provides leveled, routable log messages (far more than `print()`).
**Structured logging** emits each entry as machine-parseable data (typically JSON) instead of
free text. **Correlation IDs** tag every log line from one request with a shared identifier.
**Tracing** captures the start/end/duration of each step in a multi-step operation, showing
how the pieces fit together.

## 2. Why does it exist?

A single user request to an AI system might touch retrieval, an LLM call, and post-processing
-- three separate log lines with no way to tell they belong together, unless something ties
them to the same request. And "it printed something" isn't enough in production: you need to
filter by level, route to different destinations, query by field, and see *how long* each
step took, not just that it happened.

## 3. 💡 Mental Model

```text
logging          -> leveled, routable messages (DEBUG < INFO < WARNING < ERROR)
structured (JSON) -> each log line is DATA, not just text -- filterable/queryable
correlation ID    -> one ID stamped on every log line from the same request
tracing (spans)   -> start/end/duration per named step, nested to show structure
```

## 4. Syntax

```python
import logging

logger = logging.getLogger("my_app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
logger.addHandler(handler)

logger.info("agent started")
logger.warning("retrying")
logger.error("giving up")

# Structured (JSON) logging -- a custom Formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"level": record.levelname, "message": record.getMessage()})

# Correlation ID via contextvars (see 26-contextvars for full depth)
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
request_id_var.set("req-123")

# Tracing a step
@contextmanager
def span(name: str):
    start = time.perf_counter()
    yield
    print(f"{name} took {time.perf_counter() - start:.3f}s")
```

## 5. Minimal Example

```python
import logging

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)

logger.info("hello")  # INFO:app:hello
```

## 6. What happens internally?

```text
logger.info("agent started")
        │
        ▼
the logger checks its effective level -- INFO is >= the logger's set
level, so this message proceeds (a DEBUG call here would be silently
dropped instead)
        │
        ▼
a LogRecord object is built (message, level, logger name, timestamp, ...)
        │
        ▼
each attached Handler's Formatter renders that record into its final
string/JSON, and the handler writes it wherever it's configured to
(stdout, a file, a log aggregation service)
```

## 7. Comparison: `print()` vs `logging` vs Structured (JSON) Logging

| | `print()` | `logging` | Structured (JSON) logging |
|---|---|---|---|
| Levels/filtering | none | yes (DEBUG/INFO/WARNING/ERROR/...) | yes, same as `logging` |
| Machine-parseable? | no | not by default (free text) | yes -- each line is valid JSON |
| Multiple destinations | no | yes (multiple handlers) | yes |
| AI use case | quick local debugging | app-wide logging with levels | production log aggregation/querying by field |

## 8. 🎯 AI Engineering Use Case

Combining a correlation ID with tracing spans around an agent's retrieve → generate pipeline
produces a structured, queryable record of exactly what happened during one request.

### Example A — Tiny

```python
logger.info("agent started")
```

### Example B — Practical

```python
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"level": record.levelname, "message": record.getMessage()})
```

### Example C — AI Engineering

```python
@contextmanager
def traced_step(name: str):
    start = time.perf_counter()
    logger.info(f"{name} started", extra={"step": name})
    yield
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(f"{name} finished", extra={"step": name, "duration_ms": duration_ms})

async def run_agent(request_id: str, query: str) -> str:
    request_id_var.set(request_id)
    with traced_step("agent_run"):
        docs = await retrieve(query)
        return await generate(docs)
```

Full runnable version: [`examples/agent_pipeline_observability.py`](examples/agent_pipeline_observability.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
STRUCTURED LOGGING & TRACING
✅ Good for:
- production systems where logs need to be filtered/queried, not just read
- multi-step pipelines (agents, RAG) where you need to see WHERE time went
- correlating scattered log lines back to one originating request

❌ Avoid when:
- a quick local script's debugging output -- print() or basic logging is
  simpler and the overhead of structure isn't worth it yet
- logging so verbosely that the actual useful signal is buried in noise

BETTER ALTERNATIVE
For serious production tracing needs (distributed systems, multiple
services), reach for a real tracing library (OpenTelemetry) rather than
hand-rolling spans -- the concepts here are exactly what those tools
implement at scale.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — using `print()` for anything beyond quick local debugging**

```python
# WRONG -- no levels, no routing, no structure; can't be filtered or
# disabled without editing code, and floods stdout in production.
print(f"agent started for request {request_id}")
```

```python
# BETTER
logger.info("agent started", extra={"request_id": request_id})
```

**Mistake 2 — no correlation ID, so concurrent requests' logs are impossible to untangle**

```python
# WRONG -- with multiple concurrent requests, log lines interleave with
# no way to tell which line belongs to which request.
logger.info("retrieve started")
logger.info("generate started")
```

```python
# BETTER -- stamp every log line with the current request's ID
logger.info("retrieve started", extra={"request_id": request_id_var.get()})
```

Runnable proof of two concurrent requests staying correctly separated:
[`examples/correlation_ids.py`](examples/correlation_ids.py)

**Mistake 3 — logging only that a step happened, never how long it took**

```python
# WRONG -- tells you WHAT happened but nothing about WHERE the time went,
# which is usually the actual question when debugging a slow pipeline.
logger.info("generate finished")
```

```python
# BETTER -- log the duration too
start = time.perf_counter()
...
logger.info("generate finished", extra={"duration_ms": (time.perf_counter() - start) * 1000})
```

Runnable proof: [`examples/tracing_multi_step_pipeline.py`](examples/tracing_multi_step_pipeline.py)

## 11. ⚡ Quick Tricks

```python
# Attach extra structured fields to a single log call
logger.info("message", extra={"request_id": "req-1", "duration_ms": 42})
```

```python
# A reusable span context manager for timing any step
@contextmanager
def span(name):
    start = time.perf_counter()
    yield
    print(f"{name}: {time.perf_counter() - start:.3f}s")
```

```python
# Stop a logger's messages from ALSO going to the root logger's handlers
logger.propagate = False
```

```python
# Attach a request ID to every record automatically via a Filter
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True
```

## 12. Performance Considerations

- Building a log message (especially f-string interpolation) costs something even if the
  message is filtered out by level -- use `logger.debug("value=%s", value)` (lazy formatting)
  over `logger.debug(f"value={value}")` in genuinely hot paths, so the string is only built
  when the level actually permits it.
- Structured logging adds a small serialization cost per line (building/encoding JSON) --
  negligible next to an LLM call's latency, but worth knowing if logging becomes a bottleneck
  in a tight, high-throughput loop.

## 13. 🎤 Interview Questions

**Q: Why prefer `logging` over `print()` in production code?**
A: `logging` provides levels (so verbosity can be controlled without code changes), multiple
handlers (routing the same message to a file, stdout, and a monitoring service
simultaneously), and structured metadata via `extra=` -- none of which `print()` offers.

**Q: What problem does a correlation ID solve?**
A: Without one, log lines from concurrent requests interleave with no way to tell which
request each line belongs to. Stamping every log line from a request's handling with a shared
ID lets you filter logs down to exactly one request's full story, even under heavy concurrent
load.

**Q: What is a "span" in tracing terminology?**
A: A record of one unit of work's start time, end time, and (often) its parent span --
letting you reconstruct not just that something happened, but how long it took and how it
nested inside other work (e.g. `call_llm` nested inside `generate`, nested inside
`agent_run`).

**Q: Why would you use `contextvars` (rather than a function parameter) to propagate a
request ID through logging?**
A: Passing it as an explicit parameter would require threading it through every function
call in the chain, even ones that don't otherwise need it. A `ContextVar` lets any code
running within that request's async context read the current request ID without it being
passed down explicitly, while still staying correctly isolated between concurrent requests
(module 26 covers this mechanism in depth).

## 14. 🛠 Mini Exercise

Write a context manager `timed_step(logger, name)` that logs `"{name} started"` on entry and
`"{name} finished in {duration_ms}ms"` on exit (using `extra={"duration_ms": ...}`), and use
it to time two sequential steps in a small pipeline.

<details>
<summary>Solution</summary>

```python
import time
import logging
from contextlib import contextmanager


@contextmanager
def timed_step(logger: logging.Logger, name: str):
    start = time.perf_counter()
    logger.info(f"{name} started")
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(f"{name} finished", extra={"duration_ms": duration_ms})


logger = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO)

with timed_step(logger, "step_a"):
    time.sleep(0.01)

with timed_step(logger, "step_b"):
    time.sleep(0.02)
```

</details>

## 15. Real-World Challenge

Extend [`examples/agent_pipeline_observability.py`](examples/agent_pipeline_observability.py)
so `traced_step` also catches and logs exceptions raised inside the `with` block (as an
`ERROR`-level structured log entry including the step name and the exception message) before
re-raising -- so a failed step is just as visible in the trace as a successful one.

## 16. Cheat Sheet

```text
LOGGING & OBSERVABILITY
↓

logger = logging.getLogger("app")           named logger
logger.info("msg", extra={"k": v})           structured field on one log line
class F(logging.Formatter): def format...    custom (e.g. JSON) formatting

request_id_var: ContextVar[str]              correlation ID, propagated implicitly
request_id_var.set("req-123")

@contextmanager
def span(name):                              tracing: time + log one named step
    start = time.perf_counter()
    yield
    log(f"{name}: {time.perf_counter()-start:.3f}s")

WHEN TO USE
-> production systems needing filterable, queryable, correlatable logs

COMMON MISTAKE
-> print() debugging that survives into production with no levels or structure

AI USE CASE
-> correlation ID + traced spans around an agent's retrieve -> generate pipeline
```

---

⬅ Back to [main README](../README.md)
