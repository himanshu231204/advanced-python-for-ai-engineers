# Pattern Library

Reusable patterns that show up repeatedly across this curriculum's modules and projects,
gathered by theme instead of by module number. Each entry names the problem it solves, a
short code sketch (pulled from an already-verified example elsewhere in the repo), when to
reach for it, and where else it appears.

## Index

- [Retry with Exponential Backoff](#retry-with-exponential-backoff)
- [Circuit Breaker](#circuit-breaker)
- [Bounded Concurrent Fan-Out](#bounded-concurrent-fan-out)
- [TTL Cache](#ttl-cache)
- [Idempotency Key](#idempotency-key)
- [Correlation ID via ContextVar](#correlation-id-via-contextvar)
- [Layered Service](#layered-service)
- [Graceful Shutdown](#graceful-shutdown)
- [Liveness vs Readiness Health Checks](#liveness-vs-readiness-health-checks)
- [Typed Tool-Calling Dispatch Table](#typed-tool-calling-dispatch-table)
- [Structured Output with Validation Retry](#structured-output-with-validation-retry)
- [Streaming Pipeline (Chained Async Generators)](#streaming-pipeline-chained-async-generators)
- [RAG Orchestration](#rag-orchestration)
- [Dependency Injection via Protocol](#dependency-injection-via-protocol)

---

### Retry with Exponential Backoff

**Problem:** A transient failure (rate limit, brief network blip) shouldn't be treated as
permanent, but retrying instantly just hits the same failure again.

```python
for attempt in range(1, max_attempts + 1):
    try:
        return await call()
    except TransientError:
        if attempt == max_attempts:
            raise
        await asyncio.sleep(base_delay * (2 ** (attempt - 1)))  # exponential backoff
```

**When to use:** any call to a flaky external dependency (an LLM API, a downstream service)
where the same request is likely to succeed a moment later.

**Where it appears:** [`15-error-handling-retries`](15-error-handling-retries/),
[`projects/01-async-llm-runner`](projects/01-async-llm-runner/),
[`projects/04-agent-tool-executor`](projects/04-agent-tool-executor/).

---

### Circuit Breaker

**Problem:** Retrying a dependency that has been failing for a while just piles up latency
and load on something that's already down.

```text
CLOSED (normal) --too many failures--> OPEN (fail fast, no calls) --cooldown elapses-->
HALF_OPEN (try one call) --succeeds--> CLOSED
                          --fails----> OPEN
```

**When to use:** on top of retries, for a dependency that can go down for an extended
period — stops a struggling service from being hammered by every caller's retry loop.

**Where it appears:** [`15-error-handling-retries`](15-error-handling-retries/).

---

### Bounded Concurrent Fan-Out

**Problem:** Firing off every request at once (`asyncio.gather` over hundreds of calls) can
exhaust connections or trip a provider's rate limit.

```python
semaphore = asyncio.Semaphore(max_concurrency)

async def bounded_call(item):
    async with semaphore:
        return await call(item)

results = await asyncio.gather(*(bounded_call(i) for i in items))
```

**When to use:** any fan-out over an external API or shared resource with a real concurrency
limit.

**Where it appears:** [`12-concurrency`](12-concurrency/),
[`projects/01-async-llm-runner`](projects/01-async-llm-runner/).

---

### TTL Cache

**Problem:** Repeating an identical, expensive (and often billed) call within a short window
wastes time and money.

```python
class TTLCache:
    def get(self, key):
        entry = self._store.get(key)
        if entry is None or time.monotonic() > entry[0]:
            return None
        return entry[1]

    def set(self, key, value):
        self._store[key] = (time.monotonic() + self._ttl, value)
```

**When to use:** requests with a stable, well-defined cache key (same prompt, same model,
same parameters) that are likely to repeat.

**Where it appears:** [`16-caching`](16-caching/),
[`projects/05-production-ai-service`](projects/05-production-ai-service/).

---

### Idempotency Key

**Problem:** A client that times out waiting for a response can't tell whether the server
actually processed the request — a naive retry risks doing the (billed, stateful) work
twice.

```python
def submit(self, idempotency_key: str, payload: str) -> JobResult:
    if idempotency_key in self._seen:
        return self._seen[idempotency_key]  # replay -- no new work done
    result = do_the_real_work(payload)
    self._seen[idempotency_key] = result
    return result
```

**When to use:** any endpoint with a real side effect (submitting a job, charging something,
sending a message) that a client might retry.

**Where it appears:** [`27-production-python-patterns`](27-production-python-patterns/),
[`debugging/exercises/06-retrying-non-retryable-error`](debugging/exercises/06-retrying-non-retryable-error/)
(the related but distinct problem of knowing what's safe to retry at all).

---

### Correlation ID via ContextVar

**Problem:** Attributing a log line or a tool call to the right request/user, from code
deeply nested several calls down, without passing an ID through every function signature.

```python
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

async def handle_request(request_id: str) -> None:
    request_id_var.set(request_id)   # set once, at the top of the request
    await do_work()                   # anything called from here can read it back

def log(message: str) -> None:
    logger.info(message, extra={"request_id": request_id_var.get()})
```

**When to use:** any concurrent (async) service that needs per-request context readable
from an unpredictable, deep call chain — logging, tracing, attributing agent tool calls.
`threading.local` does NOT work here: asyncio runs every task on one thread, so it can't
tell concurrent requests apart.

**Where it appears:** [`26-contextvars`](26-contextvars/),
[`20-logging-observability`](20-logging-observability/),
[`projects/05-production-ai-service`](projects/05-production-ai-service/).

---

### Layered Service

**Problem:** A route handler that does HTTP parsing, business logic, and database access all
in one function is untestable without a real network and a real database.

```python
class DocumentRepository(Protocol):        # what data access looks like
    def get(self, doc_id: str) -> Document | None: ...

class DocumentService:                      # business logic, depends on the Protocol only
    def __init__(self, repository: DocumentRepository) -> None: ...
    def summarize(self, doc_id: str) -> str: ...

def handle_summarize_request(doc_id, service):   # the route -- translates HTTP <-> service
    ...
```

**When to use:** any service beyond a handful of trivial endpoints — each layer becomes
independently testable with the layer below it faked out.

**Where it appears:** [`27-production-python-patterns`](27-production-python-patterns/),
[`11-protocols-generics`](11-protocols-generics/),
[`projects/05-production-ai-service`](projects/05-production-ai-service/).

---

### Graceful Shutdown

**Problem:** A process killed instantly on `SIGTERM` drops whatever request it was
mid-way through handling.

```python
async def shutdown(self) -> None:
    self._shutting_down = True               # stop ACCEPTING new work first
    if self._in_flight:
        await asyncio.wait(self._in_flight, timeout=drain_timeout)   # let existing work finish
```

**When to use:** any long-running service that gets restarted (deploys, autoscaling) while
handling in-flight requests.

**Where it appears:** [`27-production-python-patterns`](27-production-python-patterns/).

---

### Liveness vs Readiness Health Checks

**Problem:** One health endpoint that checks a downstream dependency causes an orchestrator
to restart a process that's fine but just waiting on a slow database — restarting won't fix
that.

```python
@app.get("/health/live")     # "is the process responsive at all?" -- never checks deps
def liveness(): return {"status": "ok"}

@app.get("/health/ready")    # "can it currently handle traffic?" -- checks real dependencies
def readiness(): return {"status": "ready" if state.is_ready else "not_ready"}
```

**When to use:** any service running under an orchestrator (Kubernetes or similar) that
makes restart/routing decisions based on health endpoints.

**Where it appears:** [`27-production-python-patterns`](27-production-python-patterns/),
[`projects/05-production-ai-service`](projects/05-production-ai-service/).

---

### Typed Tool-Calling Dispatch Table

**Problem:** An LLM's tool call is untyped text (a name + raw arguments) — calling a real
function with those raw arguments unvalidated risks a confusing failure deep inside the
tool.

```python
class ToolRegistry:
    def register(self, name, schema, fn): self._tools[name] = (schema, fn)

    def dispatch(self, name, raw_args):
        schema, fn = self._tools[name]
        return fn(schema.model_validate(raw_args))   # validate BEFORE calling
```

**When to use:** any agent/tool-calling system, before ever invoking a tool with
model-provided arguments.

**Where it appears:** [`28-ai-engineering-patterns`](28-ai-engineering-patterns/),
[`projects/04-agent-tool-executor`](projects/04-agent-tool-executor/).

---

### Structured Output with Validation Retry

**Problem:** An LLM's JSON response isn't guaranteed to match the shape your code expects,
even when asked for "JSON mode."

```python
try:
    return Model.model_validate_json(raw_response)
except ValidationError:
    # retry with the same (or an error-augmented) prompt, don't crash outright
    ...
```

**When to use:** any pipeline that depends on an LLM producing a specific, machine-readable
shape.

**Where it appears:** [`28-ai-engineering-patterns`](28-ai-engineering-patterns/),
[`09-pydantic`](09-pydantic/).

---

### Streaming Pipeline (Chained Async Generators)

**Problem:** One function that does everything from receiving raw tokens to producing a
finished UI update is hard to test or extend.

```python
async def accumulate_text(tokens):
    buffer = ""
    async for token in tokens:
        buffer += token
        yield buffer                 # re-yield the running text, not just the newest token

async def split_into_sentences(running_text):
    async for text in running_text:
        if text.endswith("."):
            yield text                # a complete sentence, ready to render
```

**When to use:** any token-by-token streaming pipeline with more than one transformation
step between the raw source and what the client actually needs.

**Where it appears:** [`04-async-generators-streaming`](04-async-generators-streaming/),
[`28-ai-engineering-patterns`](28-ai-engineering-patterns/),
[`projects/02-streaming-llm-api`](projects/02-streaming-llm-api/).

---

### RAG Orchestration

**Problem:** Generation alone can't answer questions about private, recent, or otherwise
un-memorized information.

```python
chunks = retrieve(query)                      # 1. find relevant context
prompt = augment_prompt(query, chunks)        # 2. build a prompt that includes it
answer = await generate(prompt, client)       # 3. let the LLM answer using that context
```

**When to use:** any question-answering system where the answer depends on information the
model wasn't trained on (or shouldn't rely on memorizing).

**Where it appears:** [`28-ai-engineering-patterns`](28-ai-engineering-patterns/),
[`projects/03-concurrent-rag-pipeline`](projects/03-concurrent-rag-pipeline/).

---

### Dependency Injection via Protocol

**Problem:** Code that constructs its own dependency internally (a real LLM client, a real
database connection) can't be tested without the real thing, and can't swap providers
without editing the code that uses it.

```python
class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

def get_provider() -> ModelProvider:          # a FastAPI dependency, or any factory
    return RealProvider()

def endpoint(provider: ModelProvider = Depends(get_provider)): ...

app.dependency_overrides[get_provider] = lambda: FakeProvider()   # swap for tests
```

**When to use:** anything talking to an external, expensive, or swappable service —
especially any real LLM/vector-DB provider.

**Where it appears:** [`11-protocols-generics`](11-protocols-generics/),
[`22-dependency-injection`](22-dependency-injection/),
[`projects/06-langgraph-oriented-patterns`](projects/06-langgraph-oriented-patterns/).

---

⬅ Back to [main README](README.md)
