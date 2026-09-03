# Glossary

Short definitions for terms used throughout this curriculum, alphabetical. Each entry links
to the module where the concept is covered in full depth.

---

**async/await** — `async def` declares a coroutine function; calling it produces a coroutine
*object* that does nothing until `await`ed (or scheduled as a task). `await` runs it,
yielding control back to the event loop while waiting, and returns its result. See
[`03-asyncio`](03-asyncio/).

**async generator** — a function combining `async def` and `yield`, consumed with
`async for`. Lets real `await`-able work happen between each yielded value — the basis of
token-by-token LLM streaming. See [`04-async-generators-streaming`](04-async-generators-streaming/).

**backoff (exponential)** — increasing the delay between retry attempts (e.g. doubling each
time), so repeated failures don't hammer a struggling dependency at a constant rate. See
[`15-error-handling-retries`](15-error-handling-retries/).

**backpressure** — a mechanism that slows a producer down when a consumer can't keep up
(e.g. a bounded `asyncio.Queue` blocking `put()` once full), preventing unbounded memory
growth. See [`17-queues-background-tasks`](17-queues-background-tasks/).

**blocking call** — a synchronous call (like `time.sleep()`) that doesn't yield control back
to the event loop — placed inside an `async def`, it freezes the *entire* loop, not just
its own task. See [`03-asyncio`](03-asyncio/), [`debugging/exercises/02-blocking-call-in-async`](debugging/exercises/02-blocking-call-in-async/).

**cache (TTL / LRU)** — storing a computed result keyed by its inputs so a repeated,
identical call can be answered without redoing the work. TTL expires entries after a fixed
duration; LRU (`functools.lru_cache`) evicts the least-recently-used entry once full. See
[`16-caching`](16-caching/).

**circuit breaker** — a pattern that stops calling a dependency entirely for a cooldown
period after it fails repeatedly (CLOSED → OPEN → HALF_OPEN → CLOSED), instead of retrying
into a service that's already down. See [`15-error-handling-retries`](15-error-handling-retries/).

**closure** — a function that captures variables from its enclosing scope, remaining
accessible even after that scope has returned. The basis of decorators, memoization, and
configuration-baked callbacks. See [`01-functions`](01-functions/).

**concurrency vs. parallelism** — concurrency is *managing* multiple tasks making progress
in overlapping time (asyncio, one thread); parallelism is *literally running things at the
same time* on multiple CPU cores (multiprocessing). See [`25-gil-processes-threads`](25-gil-processes-threads/).

**ContextVar** — a variable that holds a different value per (async) execution context —
roughly one per task — instead of one shared global value. The mechanism behind correctly
isolated request-scoped state (request IDs, current user) under asyncio. See
[`26-contextvars`](26-contextvars/).

**context manager** — an object implementing `__enter__`/`__exit__` (or `__aenter__`/
`__aexit__`), used with `with`/`async with` to guarantee setup and teardown around a block,
even if it raises. See [`05-context-managers`](05-context-managers/).

**coroutine** — the object produced by calling an `async def` function. It represents a
suspendable computation that does nothing until driven by `await`, a task, or the event
loop. See [`03-asyncio`](03-asyncio/).

**correlation ID / request ID** — a unique identifier attached to one request (often via a
`ContextVar`) and included in every log line or trace span produced while handling it, so
logs from one request can be filtered out of a stream of many. See
[`20-logging-observability`](20-logging-observability/).

**dataclass** — a class decorated with `@dataclass` that auto-generates `__init__`,
`__repr__`, and `__eq__` from typed field declarations. Good for internal, trusted state;
Pydantic is the better choice once runtime validation is needed. See [`08-dataclasses`](08-dataclasses/).

**decorator** — a function that takes a function (or class) and returns a modified version
of it, applied with `@decorator` syntax. The basis of retry, caching, logging, and timing
wrappers. See [`06-decorators`](06-decorators/).

**dependency injection** — passing a dependency (a client, a service) into the code that
needs it as a parameter, instead of that code constructing it internally — makes the
dependency swappable (a real provider in production, a fake in tests). See
[`22-dependency-injection`](22-dependency-injection/).

**descriptor** — an object implementing `__get__`/`__set__`, controlling what happens when
an attribute is accessed or assigned on the class that holds it. The mechanism behind
`property` and reusable, validated attributes. See [`10-advanced-oop`](10-advanced-oop/).

**event loop** — the asyncio runtime that schedules and runs coroutines/tasks, switching
between them at `await` points. `asyncio.run()` creates and drives one for a top-level
async program. See [`03-asyncio`](03-asyncio/).

**functools.wraps** — a decorator-writing helper that copies a wrapped function's
`__name__`, `__doc__`, and other metadata onto its wrapper — omitting it silently breaks
introspection and logging that reads `fn.__name__`. See [`06-decorators`](06-decorators/),
[`debugging/exercises/04-decorator-drops-return-value`](debugging/exercises/04-decorator-drops-return-value/).

**generator** — a function containing `yield`, which pauses and resumes execution one value
at a time instead of computing everything up front. A generator is single-use: once
exhausted, iterating it again yields nothing. See [`02-iterators-generators`](02-iterators-generators/).

**GIL (Global Interpreter Lock)** — a lock in CPython ensuring only one thread executes
Python bytecode at a time, meaning `threading` cannot speed up CPU-bound pure-Python code —
only I/O-bound work benefits from it. See [`25-gil-processes-threads`](25-gil-processes-threads/).

**graceful shutdown** — stopping a process's acceptance of new work first, then waiting
(up to a deadline) for in-flight work to finish before exiting, rather than dropping
requests instantly on a termination signal. See [`27-production-python-patterns`](27-production-python-patterns/).

**health check (liveness vs. readiness)** — liveness answers "is the process responsive at
all?"; readiness answers "can it currently serve traffic?" (checking real dependencies).
Conflating the two causes unnecessary restarts. See [`27-production-python-patterns`](27-production-python-patterns/).

**HTTPX** — a Python HTTP client with both sync and async APIs (`httpx.AsyncClient`), used
throughout this repo for calling LLM/vector-DB APIs concurrently; `httpx.MockTransport`
fakes network responses for offline, deterministic tests. See [`13-httpx-async-http`](13-httpx-async-http/).

**idempotency (key)** — a property where repeating the same operation produces the same
result without additional side effects. An idempotency key lets a server recognize a
retried request and replay its original result instead of redoing the work. See
[`27-production-python-patterns`](27-production-python-patterns/).

**iterator protocol** — the `__iter__`/`__next__` pair that makes an object usable in a
`for` loop; `StopIteration` signals exhaustion. Generators implement this protocol
automatically. See [`02-iterators-generators`](02-iterators-generators/).

**keyword-only argument** — a parameter after a bare `*` (or `*args`) in a function
signature, which callers must pass by name — makes call sites self-documenting. See
[`01-functions`](01-functions/).

**mutable default argument** — a classic bug: a default value like `[]` or `{}` is created
*once*, at function-definition time, and shared (and silently mutated) across every call
that relies on it. See [`01-functions`](01-functions/), [`code-reading/exercises/04-mutability-shared-references`](code-reading/exercises/04-mutability-shared-references.md).

**Protocol** — a `typing.Protocol` class defining a structural "shape" (methods/attributes)
without requiring inheritance — any object matching the shape satisfies it. Enables
swappable providers/tools with zero coupling to a base class. See [`11-protocols-generics`](11-protocols-generics/).

**Pydantic (BaseModel)** — a library for declaring typed data models that *validate* at
runtime, raising a clear `ValidationError` on bad input instead of failing silently or deep
inside unrelated code. The standard way to validate LLM output, API bodies, and config in
this curriculum. See [`09-pydantic`](09-pydantic/).

**pydantic-settings (BaseSettings)** — a Pydantic subclass that reads and validates
configuration from environment variables (and `.env` files) into one typed object, loaded
once at startup instead of scattered `os.environ` reads. See [`21-config-environments`](21-config-environments/).

**queue (asyncio.Queue)** — an async-safe buffer between producer(s) and consumer(s); a
bounded queue (`maxsize=N`) provides backpressure instead of growing without limit. See
[`17-queues-background-tasks`](17-queues-background-tasks/).

**RAG (Retrieval-Augmented Generation)** — retrieving relevant context (from a vector store,
keyword index, etc.), inserting it into a prompt, then generating an answer grounded in
that context — lets an LLM answer questions about information it wasn't trained on. See
[`28-ai-engineering-patterns`](28-ai-engineering-patterns/).

**retry** — re-attempting a failed operation, ideally only for failures classified as
*transient* (rate limits, timeouts) and never for failures that will always recur the same
way (bad auth, a malformed request). See [`15-error-handling-retries`](15-error-handling-retries/).

**semaphore (asyncio.Semaphore)** — a primitive that limits how many concurrent tasks can
hold it at once (`async with semaphore:`), used to bound fan-out against a rate-limited or
resource-limited dependency. See [`12-concurrency`](12-concurrency/).

**serialization** — converting an in-memory object into a storable/transmittable form
(JSON text, bytes) and back. `json` handles JSON-native types only; Pydantic's
`model_dump_json`/`model_validate_json` also handle dates, enums, and nested models. See
[`18-serialization`](18-serialization/).

**slots (`__slots__` / `@dataclass(slots=True)`)** — declaring a class's exact attribute
set up front, replacing its per-instance `__dict__` with fixed storage — saves memory and
prevents accidentally setting an undeclared attribute. See [`08-dataclasses`](08-dataclasses/).

**SSE (Server-Sent Events)** — a one-way HTTP streaming protocol where the server pushes
`data: ...\n\n`-formatted events to the client over a single long-lived connection — used
for streaming an LLM completion token by token. See [`14-streaming-sse-websockets`](14-streaming-sse-websockets/).

**structural typing** — typing based on an object's *shape* (its methods/attributes) rather
than its declared class hierarchy — what `Protocol` provides in Python. See
[`11-protocols-generics`](11-protocols-generics/).

**structured output** — treating an LLM's response as data with an expected schema (via a
Pydantic model) rather than free text to be parsed ad hoc, so a mismatch surfaces as one
clear validation error. See [`28-ai-engineering-patterns`](28-ai-engineering-patterns/).

**TaskGroup (asyncio.TaskGroup)** — structured concurrency: a context manager that runs
multiple tasks together and automatically cancels the remaining siblings if one fails,
avoiding orphaned background tasks. See [`12-concurrency`](12-concurrency/).

**threading.local** — storage that holds a different value *per OS thread*. It does **not**
correctly isolate per-request state under asyncio, because every task in an asyncio program
runs on the same thread — see `ContextVar` instead. See [`26-contextvars`](26-contextvars/).

**tool calling** — an LLM emitting a structured request to call a named function with given
arguments; the calling code is responsible for validating those arguments before actually
invoking the real function. See [`28-ai-engineering-patterns`](28-ai-engineering-patterns/).

**TypedDict** — a `typing` construct describing a `dict`'s expected keys and value types,
for static type checking — unlike Pydantic, it performs **no** runtime validation. See
[`07-type-hints`](07-type-hints/).

**TypeVar / generics** — `TypeVar` parameterizes a function or class over an unspecified
type (`Stack[T]`), letting the same code work correctly and type-safely across many
concrete types. See [`11-protocols-generics`](11-protocols-generics/).

**ValidationError** — the exception Pydantic raises when data doesn't match a model's
declared shape/constraints, carrying a structured list of every field that failed. See
[`09-pydantic`](09-pydantic/).

**WebSocket** — a bidirectional, persistent connection protocol, used (unlike one-way SSE)
for multi-turn interactive sessions like an agent chat. See
[`14-streaming-sse-websockets`](14-streaming-sse-websockets/).

**yield / yield from** — `yield` pauses a generator function and produces one value;
`yield from` delegates iteration to a nested generator/iterable, forwarding its values
(and, for coroutines pre-`async`/`await`, its sent values and return value) transparently.
See [`02-iterators-generators`](02-iterators-generators/).

---

⬅ Back to [main README](README.md)
