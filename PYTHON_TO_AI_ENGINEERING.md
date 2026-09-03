# Python → AI Engineering Map

The other reference docs are organized by module ([`CHEATSHEET.md`](CHEATSHEET.md),
[`INTERVIEW.md`](INTERVIEW.md)) or by pattern ([`PATTERNS.md`](PATTERNS.md)). This one is
organized by **AI-engineering task** — pick the thing you're building, and see which Python
concepts it actually depends on and why.

## Index

- [Calling an LLM or vector-DB API](#calling-an-llm-or-vector-db-api)
- [Streaming a response to a client](#streaming-a-response-to-a-client)
- [Validating LLM output](#validating-llm-output)
- [Running many LLM calls concurrently, safely](#running-many-llm-calls-concurrently-safely)
- [Building a tool-calling agent](#building-a-tool-calling-agent)
- [Reducing repeated LLM cost and latency](#reducing-repeated-llm-cost-and-latency)
- [Retrieval-Augmented Generation (RAG)](#retrieval-augmented-generation-rag)
- [Attributing state across concurrent requests](#attributing-state-across-concurrent-requests)
- [Keeping an AI service alive under real traffic](#keeping-an-ai-service-alive-under-real-traffic)
- [Testing AI code without hitting real APIs](#testing-ai-code-without-hitting-real-apis)
- [Packaging and shipping an AI project](#packaging-and-shipping-an-ai-project)
- [Understanding performance and scaling tradeoffs](#understanding-performance-and-scaling-tradeoffs)

---

### Calling an LLM or vector-DB API

Every AI system eventually makes an HTTP call to something slow and occasionally unreliable.

- [`03-asyncio`](03-asyncio/) — `await` the call instead of blocking the whole process on it.
- [`13-httpx-async-http`](13-httpx-async-http/) — a real async HTTP client, reused across
  calls for connection pooling.
- [`15-error-handling-retries`](15-error-handling-retries/) — classify failures, retry only
  the transient ones, back off, and fail fast on the rest.

### Streaming a response to a client

Users expect to see an LLM's answer appear token by token, not all at once after a long wait.

- [`02-iterators-generators`](02-iterators-generators/) — the iterator protocol streaming is
  built on.
- [`04-async-generators-streaming`](04-async-generators-streaming/) — `async for` over
  tokens as they arrive.
- [`14-streaming-sse-websockets`](14-streaming-sse-websockets/) — SSE for one-way streaming,
  WebSockets for a bidirectional agent chat.

### Validating LLM output

An LLM's response is untrusted, unstructured text even when you ask for JSON — treat it like
any other external input.

- [`07-type-hints`](07-type-hints/) — the vocabulary for describing expected shapes.
- [`09-pydantic`](09-pydantic/) — actually validate at runtime, with a clear error on
  mismatch.
- [`28-ai-engineering-patterns`](28-ai-engineering-patterns/) — the structured-output +
  retry-on-`ValidationError` pattern, end to end.

### Running many LLM calls concurrently, safely

Batch summarization, parallel tool calls, and fan-out retrieval all need more than one
in-flight request at a time — but not unlimited ones.

- [`12-concurrency`](12-concurrency/) — `asyncio.gather`, `TaskGroup`, and semaphores to
  bound how many run at once.
- [`15-error-handling-retries`](15-error-handling-retries/) — one failed call in a batch
  shouldn't take down the rest.
- [`projects/01-async-llm-runner`](projects/01-async-llm-runner/) — all of the above
  combined into one runnable project.

### Building a tool-calling agent

An agent deciding to call `search_docs` or `send_email` is really just dispatching on a
name with untyped arguments.

- [`11-protocols-generics`](11-protocols-generics/) — a typed, swappable tool interface with
  no shared base class required.
- [`10-advanced-oop`](10-advanced-oop/) — `__call__` for stateful tool objects that behave
  like functions.
- [`28-ai-engineering-patterns`](28-ai-engineering-patterns/) — the validated
  dispatch-table pattern tying a tool call's name and arguments to a real function safely.
- [`projects/04-agent-tool-executor`](projects/04-agent-tool-executor/) — a full executor
  with retries around tool calls.

### Reducing repeated LLM cost and latency

The same prompt (or an equivalent one) is often asked more than once in a short window —
every repeated, billed call is waste.

- [`16-caching`](16-caching/) — `functools.lru_cache` for pure functions, a TTL cache for
  time-bound repeats.
- [`27-production-python-patterns`](27-production-python-patterns/) — idempotency keys, the
  related concern of not re-doing work on a client retry.

### Retrieval-Augmented Generation (RAG)

Answering questions about information the model wasn't trained on requires combining search
with generation.

- [`12-concurrency`](12-concurrency/) — fan out to multiple retrieval sources at once.
- [`13-httpx-async-http`](13-httpx-async-http/) — calling a real vector DB or search API.
- [`28-ai-engineering-patterns`](28-ai-engineering-patterns/) — the
  retrieve → augment → generate orchestration shape.
- [`projects/03-concurrent-rag-pipeline`](projects/03-concurrent-rag-pipeline/) — a full,
  timeout-tolerant pipeline.

### Attributing state across concurrent requests

Logging or attributing a tool call to the right user, when many requests are being handled
"at once" on one event loop, is not the same problem it is in single-threaded sync code.

- [`26-contextvars`](26-contextvars/) — `ContextVar`, the mechanism that actually isolates
  this correctly under asyncio (`threading.local` does not).
- [`20-logging-observability`](20-logging-observability/) — correlation IDs and structured
  logs built on top of it.

### Keeping an AI service alive under real traffic

A service that works in a demo still needs to survive deploys, restarts, and dependency
outages once it's live.

- [`21-config-environments`](21-config-environments/) — one validated settings object
  instead of scattered environment reads.
- [`17-queues-background-tasks`](17-queues-background-tasks/) — long-running jobs (batch
  embedding, evals) off the request path.
- [`27-production-python-patterns`](27-production-python-patterns/) — layering, graceful
  shutdown, health checks, idempotency, all in one place.
- [`projects/05-production-ai-service`](projects/05-production-ai-service/) — all of the
  above combined into one deployable service.

### Testing AI code without hitting real APIs

A test suite that calls a real LLM API is slow, flaky, and costs money on every run.

- [`19-testing-pytest`](19-testing-pytest/) — fixtures, async tests, and mocking outbound
  calls with `httpx.MockTransport`.
- [`22-dependency-injection`](22-dependency-injection/) — swap a real provider for a fixed
  fake at the seam, rather than patching internals.

### Packaging and shipping an AI project

Every module and project in this repo has its own reproducible dependency story — that's
not an accident.

- [`23-packaging-modern-python`](23-packaging-modern-python/) — `pyproject.toml`, `uv`,
  `ruff`, and the `src/` layout used across this repo's own project folders.

### Understanding performance and scaling tradeoffs

Not every slow AI workload is an I/O problem — knowing which kind you have decides the fix.

- [`24-performance-memory`](24-performance-memory/) — identity vs. equality, shallow vs.
  deep copy, and profiling to find out where time actually goes.
- [`25-gil-processes-threads`](25-gil-processes-threads/) — why threads don't speed up
  CPU-bound preprocessing/embedding work, and when `multiprocessing` is the real fix.

---

⬅ Back to [main README](README.md)
