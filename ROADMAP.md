# Roadmap

A phased path through this repository. The numbered modules are designed to be worked
top-to-bottom (that's the default, recommended path in the main [`README.md`](README.md)) —
this document adds pacing, checkpoints, and an alternative order for readers who already
know foundational Python and want to reach AI-system content sooner.

---

## Before you start

Skim [`00-python-foundation-review`](00-python-foundation-review/) first. If everything in
it is already familiar, move straight to Phase 1 — this repository does not re-teach
basic Python (see `AGENTS.md` §10 for exactly what's out of scope).

## Phase 1 — Core Async & Functional Python (Level 1)

The mechanics almost everything later depends on: how functions actually work, how
generators and `async`/`await` execute, and the two protocols (context managers,
decorators) that show up everywhere in real codebases.

| Module | Why it matters before anything else |
|---|---|
| [`01-functions`](01-functions/) | closures, `*args`/`**kwargs`, mutable defaults |
| [`02-iterators-generators`](02-iterators-generators/) | the iterator protocol asyncio and streaming build on |
| [`03-asyncio`](03-asyncio/) | coroutines, the event loop, concurrent I/O |
| [`04-async-generators-streaming`](04-async-generators-streaming/) | `async for`, token-by-token streaming |
| [`05-context-managers`](05-context-managers/) | `with`/`async with`, resource cleanup |
| [`06-decorators`](06-decorators/) | how retry/caching/logging wrappers are actually built |

**Checkpoint:** you should be able to explain, from memory, why `await` is required, what a
generator's `yield` actually pauses, and what `functools.wraps` fixes.

## Phase 2 — Typed, Structured Python (Level 2)

Turns "code that runs" into code with an explicit, checkable shape — the layer LLM/agent
systems lean on heavily for validating untrusted model output.

| Module | Why it matters |
|---|---|
| [`07-type-hints`](07-type-hints/) | the vocabulary every later module's signatures use |
| [`08-dataclasses`](08-dataclasses/) | lightweight structured data before reaching for Pydantic |
| [`09-pydantic`](09-pydantic/) | validating LLM output, API requests, config |
| [`11-protocols-generics`](11-protocols-generics/) | structural typing — swappable providers/tools |
| [`18-serialization`](18-serialization/) | JSON, `pathlib`, saving/loading state |
| [`19-testing-pytest`](19-testing-pytest/) | fixtures, async tests, mocking LLM calls |
| [`21-config-environments`](21-config-environments/) | validated settings instead of scattered `os.environ` |
| [`22-dependency-injection`](22-dependency-injection/) | swappable services for testing and providers |
| [`23-packaging-modern-python`](23-packaging-modern-python/) | `pyproject.toml`, `uv`, `ruff` |

**Checkpoint:** you should be comfortable reaching for a Pydantic model over a raw `dict`
any time data crosses a boundary (an API request, an LLM response, a config file).

## Phase 3 — AI-System Python (Level 3)

The patterns specific to building and operating LLM/RAG/agent services: concurrency at
scale, HTTP to model providers, streaming to a client, and everything that keeps a service
alive under real traffic.

| Module | Why it matters |
|---|---|
| [`12-concurrency`](12-concurrency/) | bounded fan-out, `TaskGroup`, semaphores |
| [`13-httpx-async-http`](13-httpx-async-http/) | calling LLM/vector-DB APIs asynchronously |
| [`14-streaming-sse-websockets`](14-streaming-sse-websockets/) | streaming tokens to a client |
| [`15-error-handling-retries`](15-error-handling-retries/) | backoff, circuit breakers, retryable vs not |
| [`16-caching`](16-caching/) | avoiding repeated, billed LLM calls |
| [`17-queues-background-tasks`](17-queues-background-tasks/) | long-running jobs off the request path |
| [`20-logging-observability`](20-logging-observability/) | correlation IDs, structured logs, tracing |
| [`27-production-python-patterns`](27-production-python-patterns/) | layering, graceful shutdown, health checks, idempotency |
| [`28-ai-engineering-patterns`](28-ai-engineering-patterns/) | tool calling, structured output, RAG orchestration, eval harnesses |

**Checkpoint:** attempt [`projects/01-async-llm-runner`](projects/01-async-llm-runner/)
through [`projects/04-agent-tool-executor`](projects/04-agent-tool-executor/) once you've
covered their listed prerequisite modules — see [`projects/README.md`](projects/README.md).

## Phase 4 — Deep Python (Level 4)

The internals that explain *why* the above patterns exist and where they stop applying —
optional depth once the practical layers are solid, but high-value for interviews.

| Module | Why it matters |
|---|---|
| [`10-advanced-oop`](10-advanced-oop/) | descriptors, dunder methods, operator overloading |
| [`24-performance-memory`](24-performance-memory/) | reference counting, GC, profiling |
| [`25-gil-processes-threads`](25-gil-processes-threads/) | why threads don't speed up CPU-bound work |
| [`26-contextvars`](26-contextvars/) | how request-scoped state survives `await` correctly |

**Checkpoint:** attempt [`projects/05-production-ai-service`](projects/05-production-ai-service/)
and [`projects/06-langgraph-oriented-patterns`](projects/06-langgraph-oriented-patterns/) —
by this point every module they draw on has been covered.

## Ongoing, at any phase

- [`code-reading/`](code-reading/) — predict-the-output exercises. Do these alongside
  whatever module they relate to, or as a standalone drill.
- [`debugging/`](debugging/) — broken/fixed pairs. Same as above — no prerequisite phase.

## Alternative path: already know foundational Python

If closures, generators, and `async`/`await` are already comfortable, skip straight to
Phase 2, treating Phase 1 as reference material to check back against rather than a
sequential read. Everything in Phase 3 still assumes Phase 2's typed/validated mindset, so
don't skip that phase even when jumping ahead.

## Suggested pace

A reasonable full-time pace is roughly one module per day, including running every example
and attempting the mini exercise — faster for a familiar topic, slower for Phase 4. At that
pace: Phase 1 in a week, Phase 2 in under two weeks, Phase 3 in about two weeks, Phase 4 in
under a week, leaving the six projects as a final ~1-2 week capstone stretch.

---

⬅ Back to [main README](README.md)
