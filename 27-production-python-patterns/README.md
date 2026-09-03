# 27 — Production Python Patterns

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

Everything so far has focused on individual language features. This module is about the
patterns that turn correct code into a service that survives real traffic, restarts, bad
input, and slow dependencies -- layering, graceful shutdown, health checks, config
discipline, and idempotency.

> Examples in this module need `fastapi`, `httpx`, and `pydantic-settings`. See
> [`requirements.txt`](requirements.txt).

---

## 1. What is it?

A production Python service is not just "code that works when you run it once." It's code
that: starts up predictably, tells an orchestrator honestly whether it's healthy, shuts down
without dropping in-flight work, reads its configuration from one validated place, and
survives clients retrying the same request. Each of those is a small, well-known pattern.

## 2. Why does it exist?

Real deployments restart processes constantly (deploys, autoscaling, crashes), route traffic
based on health signals, and run behind clients that retry on timeout. Code that ignores all
of this works fine in a demo and then loses requests, double-charges an LLM API, or gets
killed mid-response the first time it meets production traffic.

## 3. 💡 Mental Model

```text
naive script                         production service
------------                         -------------------
one os.environ.get() per call site   ONE validated Settings object at startup
route handler does everything        route -> service -> repository layers
SIGTERM -> process dies instantly    SIGTERM -> stop new work, drain, THEN exit
"is it up?" == "did it crash?"       liveness (process ok) vs readiness (can serve traffic)
retry = redo the side effect         retry with idempotency key = replay the same result
```

## 4. Syntax

```python
# Layering: route depends on service depends on a Protocol, not a concrete DB
class DocumentService:
    def __init__(self, repository: DocumentRepository) -> None: ...

# Graceful shutdown: stop taking work, then wait for what's already running
async def shutdown(self) -> None:
    self._shutting_down = True
    await asyncio.wait(self._in_flight, timeout=drain_timeout)

# Health checks: two separate endpoints, two separate questions
@app.get("/health/live")   # is the process responsive at all?
@app.get("/health/ready")  # can it currently handle real traffic?

# Config discipline: one Settings object, validated once
class Settings(BaseSettings):
    llm_api_key: str
    llm_timeout_seconds: float = Field(default=30.0, gt=0)

# Idempotency: same key in -> same result out, no repeated side effect
def submit(self, idempotency_key: str, payload: str) -> JobResult: ...
```

## 5. Minimal Example

```python
from dataclasses import dataclass

@dataclass
class JobResult:
    job_id: str

class JobSubmitter:
    def __init__(self) -> None:
        self._seen: dict[str, JobResult] = {}

    def submit(self, key: str, payload: str) -> JobResult:
        if key in self._seen:
            return self._seen[key]
        result = JobResult(job_id=f"job-{len(self._seen) + 1}")
        self._seen[key] = result
        return result
```

## 6. What happens internally? (shutdown sequence)

```text
SIGTERM received
      │
      ▼
set self._shutting_down = True   -- new requests get rejected from here on
      │
      ▼
await asyncio.wait(in_flight_tasks, timeout=drain_timeout)
      │                                   │
      ▼                                   ▼
   all finished in time            timeout hit -- log which
   before deadline                 tasks were force-cancelled
      │                                   │
      └──────────────┬────────────────────┘
                      ▼
              process exits cleanly
```

## 7. Comparison: naive approach vs the production pattern

| Concern | Naive approach | Production pattern | Failure without it |
|---|---|---|---|
| Structure | route handler does DB + logic + response | route → service → repository layers | untestable, DB-coupled business logic |
| Shutdown | process just dies on SIGTERM | drain in-flight work first | requests silently dropped mid-response |
| Health | one `/health` returns "ok" always | separate liveness vs readiness | orchestrator restarts a pod that's just waiting on a slow DB |
| Config | `os.environ.get(...)` scattered everywhere | one validated `Settings` object | a typo'd env var surfaces as a 500 three calls deep, not at startup |
| Retries | client retry re-runs the side effect | idempotency key replays the stored result | a retried "charge card" or "submit job" request happens twice |

## 8. 🎯 AI Engineering Use Case

An AI service is retried constantly (client timeouts on slow LLM calls), restarted often
(rolling deploys), and depends on external, sometimes-slow services (the LLM API, a vector
DB) -- exactly the conditions these patterns exist for.

### Example A — Tiny

```python
class Settings(BaseSettings):
    llm_api_key: str
```

### Example B — Practical

```python
@app.get("/health/ready")
def readiness() -> dict:
    return {"status": "ready"} if state.is_ready else {"status": "not_ready"}
```

### Example C — AI Engineering

```python
def submit(self, idempotency_key: str, payload: str) -> JobResult:
    """A client retrying an embedding-job submission after a timeout must
    get back the SAME job, not trigger a second (billed) embedding call."""
    if idempotency_key in self._seen:
        return self._seen[idempotency_key]
    ...
```

Full runnable versions:
[`examples/service_layering.py`](examples/service_layering.py),
[`examples/graceful_shutdown.py`](examples/graceful_shutdown.py),
[`examples/health_checks.py`](examples/health_checks.py),
[`examples/config_discipline.py`](examples/config_discipline.py),
[`examples/idempotency.py`](examples/idempotency.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
PRODUCTION PYTHON PATTERNS
✅ Good for:
- any service that will be deployed, restarted, or scaled -- even a small internal tool
- endpoints backed by slow/unreliable dependencies (LLM APIs, vector DBs, external tools)
- any endpoint that has a side effect a client might trigger twice via retry

❌ Avoid when:
- a one-off script that runs once and exits -- graceful shutdown and health checks add
  nothing there
- prototyping/exploration code not headed for a real deployment yet

BETTER ALTERNATIVE
Keep prototypes simple and add these patterns when the code is actually about to run
behind real traffic -- retrofitting later is fine, over-engineering a throwaway script
isn't.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — one `/health` endpoint answering both liveness and readiness**

```python
# WRONG -- a temporarily slow vector DB makes the orchestrator kill and
# restart a perfectly healthy process, which won't fix a slow DB.
@app.get("/health")
def health():
    return {"ok": check_vector_db_connection()}
```

```python
# BETTER -- separate the two questions
@app.get("/health/live")
def liveness():
    return {"status": "ok"}  # process can respond at all

@app.get("/health/ready")
def readiness():
    return {"status": "ready" if check_vector_db_connection() else "not_ready"}
```

**Mistake 2 — reading config with scattered `os.environ.get()` calls**

```python
# WRONG -- a typo'd or missing var surfaces as a confusing error deep in
# a request, not a clear failure at startup.
timeout = float(os.environ.get("LLM_TIMEOUT_SECONDS", 30))
```

```python
# BETTER -- one validated Settings object, loaded once, fails loudly at startup
class Settings(BaseSettings):
    llm_timeout_seconds: float = Field(default=30.0, gt=0)

settings = Settings()  # raises ValidationError immediately if misconfigured
```

**Mistake 3 — no idempotency key on an endpoint with a real side effect**

```python
# WRONG -- a client retry after a timeout submits the job AGAIN, even
# though the server already processed the first attempt.
@app.post("/jobs")
def submit_job(payload: JobPayload):
    return run_job(payload)  # runs every time this is called
```

```python
# BETTER -- the same idempotency key returns the original result
@app.post("/jobs")
def submit_job(payload: JobPayload, idempotency_key: str):
    return job_submitter.submit(idempotency_key, payload)
```

Runnable proof: [`examples/idempotency.py`](examples/idempotency.py)

## 11. ⚡ Quick Tricks

```python
# Fail fast on bad config instead of catching it later
try:
    settings = Settings()
except ValidationError as exc:
    raise SystemExit(f"invalid configuration: {exc}") from exc
```

```python
# Depend on a Protocol, not a concrete class, for testable layering
class DocumentRepository(Protocol):
    def get(self, doc_id: str) -> Document | None: ...
```

```python
# Track in-flight work so shutdown has something to drain
task = asyncio.current_task()
in_flight.add(task)
try:
    ...
finally:
    in_flight.discard(task)
```

## 12. Performance Considerations

- Loading and validating config once at startup (rather than on every request) is both
  faster and safer -- there's no per-request parsing cost, and no chance of the app running
  for hours before a misconfigured value is even read.
- Draining in-flight requests during shutdown should have a hard timeout -- an unbounded
  drain can hang a deploy indefinitely if one request is stuck.
- Health check endpoints should be cheap. A readiness check that itself makes a full LLM
  call on every poll adds real load and cost for no benefit -- check a cached "last known
  good" status instead.

## 13. 🎤 Interview Questions

**Q: What's the difference between a liveness and a readiness check?**
A: Liveness asks "is this process responsive, or should it be killed and restarted?"
Readiness asks "can this process currently handle real traffic?" A pod can be alive (not
deadlocked) but not ready (its database connection is down) -- conflating the two causes an
orchestrator to restart pods that just need traffic paused, not a restart.

**Q: Why does layering (route → service → repository) matter for testability?**
A: The service layer depends on a repository *Protocol*, not a concrete database client, so
tests can substitute an in-memory fake with no network or database needed -- the business
logic is tested in isolation from I/O.

**Q: Why is an idempotency key necessary even if your server never fails mid-request?**
A: The failure mode it protects against is on the *client* side: the client's connection can
time out or drop after the server already processed the request but before the response
arrived. The client, unable to tell success from failure, retries -- an idempotency key lets
the server recognize the retry and return the original result instead of repeating the side
effect.

**Q: Why load configuration into one validated object instead of reading environment
variables inline throughout the codebase?**
A: A single validated object fails loudly and immediately at startup if configuration is
missing or malformed, rather than surfacing as a confusing runtime error deep inside a
request handler hours or days after deploy.

## 14. 🛠 Mini Exercise

Extend `JobSubmitter` (from [`examples/idempotency.py`](examples/idempotency.py)) with a
`status(idempotency_key: str) -> str` method that returns `"unknown"` for a key that was
never submitted, and the stored job's status otherwise.

<details>
<summary>Solution</summary>

```python
class JobSubmitter:
    def __init__(self) -> None:
        self._seen: dict[str, JobResult] = {}
        self._next_id = 1

    def submit(self, idempotency_key: str, payload: str) -> JobResult:
        if idempotency_key in self._seen:
            return self._seen[idempotency_key]
        job_id = f"job-{self._next_id}"
        self._next_id += 1
        result = JobResult(job_id=job_id, status=f"submitted: {payload}")
        self._seen[idempotency_key] = result
        return result

    def status(self, idempotency_key: str) -> str:
        result = self._seen.get(idempotency_key)
        return "unknown" if result is None else result.status


submitter = JobSubmitter()
print(submitter.status("req-abc"))          # unknown
submitter.submit("req-abc", "embed doc 42")
print(submitter.status("req-abc"))          # submitted: embed doc 42
```

</details>

## 15. Real-World Challenge

Add a `max_drain_seconds` limit to [`examples/graceful_shutdown.py`](examples/graceful_shutdown.py)'s
`shutdown()` that logs which specific requests were still in-flight when the timeout was hit
(rather than silently discarding them), so an operator can see exactly what got interrupted.

## 16. Cheat Sheet

```text
PRODUCTION PYTHON PATTERNS
↓

LAYERING          route -> service -> repository (Protocol), each layer testable alone
SHUTDOWN          set a "stop accepting work" flag, THEN await draining in-flight tasks
HEALTH            /health/live = "is the process ok?", /health/ready = "can it serve traffic?"
CONFIG            one validated Settings object, loaded once, fails loudly at startup
IDEMPOTENCY       same idempotency key in -> same stored result out, no repeated side effect

WHEN TO USE
-> any service headed for real deployment, restarts, autoscaling, or retrying clients

COMMON MISTAKE
-> one health endpoint answering both liveness and readiness

AI USE CASE
-> AI services face slow dependencies, frequent restarts, and client retries constantly --
   these patterns are what keeps them from double-billing an LLM call or dropping requests
```

---

⬅ Back to [main README](../README.md)
