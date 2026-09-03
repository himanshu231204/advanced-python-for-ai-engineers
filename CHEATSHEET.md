# Cheat Sheet

The condensed "Cheat Sheet" section from every written module, in one scannable page —
useful as a quick reference or a pre-interview skim. Each entry links back to its full
module for the complete explanation, examples, and interview questions.

`00-python-foundation-review` is still a stub (not yet written) and has no entry here yet.

## Index

- [01 — Functions](#01--functions)
- [02 — Iterators & Generators](#02--iterators--generators)
- [03 — Asyncio Fundamentals](#03--asyncio-fundamentals)
- [04 — Async Generators & Streaming](#04--async-generators--streaming)
- [05 — Context Managers](#05--context-managers)
- [06 — Decorators](#06--decorators)
- [07 — Type Hints](#07--type-hints)
- [08 — Dataclasses](#08--dataclasses)
- [09 — Pydantic](#09--pydantic)
- [10 — Advanced OOP & Magic Methods](#10--advanced-oop--magic-methods)
- [11 — Protocols & Generics](#11--protocols--generics)
- [12 — Concurrency](#12--concurrency)
- [13 — HTTPX & Async HTTP](#13--httpx--async-http)
- [14 — Streaming: SSE & WebSockets](#14--streaming-sse--websockets)
- [15 — Error Handling & Retries](#15--error-handling--retries)
- [16 — Caching](#16--caching)
- [17 — Queues & Background Tasks](#17--queues--background-tasks)
- [18 — Serialization](#18--serialization)
- [19 — Testing with Pytest](#19--testing-with-pytest)
- [20 — Logging & Observability](#20--logging--observability)
- [21 — Configuration & Environments](#21--configuration--environments)
- [22 — Dependency Injection](#22--dependency-injection)
- [23 — Packaging & Modern Python Tooling](#23--packaging--modern-python-tooling)
- [24 — Performance & Memory](#24--performance--memory)
- [25 — GIL, Processes & Threads](#25--gil-processes--threads)
- [26 — Contextvars](#26--contextvars)
- [27 — Production Python Patterns](#27--production-python-patterns)
- [28 — AI Engineering Patterns](#28--ai-engineering-patterns)

---

### 01 — Functions

[Full module →](01-functions/)


```text
FUNCTIONS
↓
def f(a, b=1, *args, c, d=2, **kwargs): ...
     │  │      │       │  │      │
     │  │      │       │  │      └─ extra kwargs -> dict
     │  │      │       │  └─ keyword-only, has default
     │  │      │       └─ keyword-only, required
     │  │      └─ extra positionals -> tuple
     │  └─ positional-or-keyword, has default
     └─ positional-or-keyword, required

WHEN TO USE *args/**kwargs
-> forwarding to a wrapped function, generic tool dispatch

COMMON MISTAKE
-> mutable default argument (list/dict) shared across calls

AI USE CASE
-> dispatch_tool_call(name, **arguments)  # LLM tool-calling
```

### 02 — Iterators & Generators

[Full module →](02-iterators-generators/)


```text
ITERATORS & GENERATORS
↓

class C:                    def gen():                (x for x in range(n))
    def __iter__(self): ...     while cond:            generator expression --
    def __next__(self): ...        yield value         lazy, near-zero memory

WHEN TO USE
-> streaming data, large/infinite sequences, one-pass pipelines

COMMON MISTAKE
-> reusing an exhausted generator (silently returns nothing, no error)

AI USE CASE
-> stream_tokens(llm_response)  # yield one token at a time instead of returning it all
```

### 03 — Asyncio Fundamentals

[Full module →](03-asyncio/)


```text
ASYNCIO FUNDAMENTALS
↓

async def f(): ...       defines a coroutine FUNCTION
f()                       calling it -> a coroutine OBJECT (nothing runs yet)
await f()                 runs it, yields control while waiting, returns its result
asyncio.run(main())       entry point for a top-level async program
asyncio.sleep(n)          non-blocking wait -- yields control back to the loop
asyncio.gather(*coros)    run multiple coroutines concurrently, wait for all results

WHEN TO USE
-> I/O-bound work: HTTP calls, DB queries, concurrent API fan-out

COMMON MISTAKE
-> time.sleep() or any blocking call inside async code freezes the WHOLE event loop

AI USE CASE
-> await asyncio.gather(llm_call(), vector_db_call(), search_call())
   # pay for the slowest call, not the sum of all three
```

### 04 — Async Generators & Streaming

[Full module →](04-async-generators-streaming/)


```text
ASYNC GENERATORS & STREAMING
↓

async def gen():              class C:
    while cond:                    def __aiter__(self): return self
        await something()          async def __anext__(self): ...
        yield value

async for x in gen():         consume with async for, not for

WHEN TO USE
-> streaming data with real async work between values (LLM tokens, websocket events)

COMMON MISTAKE
-> a blocking call (time.sleep) inside an async generator freezes the whole event loop

AI USE CASE
-> async for token in stream_llm_tokens(response): send_to_client(token)
```

### 05 — Context Managers

[Full module →](05-context-managers/)


```text
CONTEXT MANAGERS
↓

class C:                       @contextmanager
    def __enter__(self): ...   def resource():
    def __exit__(self, *exc):      setup()
        ...                        try:
        return False                   yield value
                                    finally:
                                        teardown()

async with httpx.AsyncClient() as client:
    ...

WHEN TO USE
-> anything with an open/close, acquire/release lifecycle

COMMON MISTAKE
-> __exit__ returning True unconditionally silently swallows ALL exceptions

AI USE CASE
-> async with llm_client() as client: ...  # guarantees cleanup even on failure
```

### 06 — Decorators

[Full module →](06-decorators/)


```text
DECORATORS
↓

def decorator(fn):              def retry(times):        class CountCalls:
    @functools.wraps(fn)            def decorator(fn):        def __init__(self, fn):
    def wrapper(*a, **kw):              @functools.wraps(fn)      functools.update_wrapper(self, fn)
        ...                             def wrapper(*a, **kw):     self.fn = fn
        return fn(*a, **kw)                 ...                def __call__(self, *a, **kw):
    return wrapper                      return wrapper             return self.fn(*a, **kw)
                                     return decorator

WHEN TO USE
-> cross-cutting concerns applied across many functions (retry, logging, timing)

COMMON MISTAKE
-> forgetting functools.wraps -- loses __name__/__doc__ on the decorated function

AI USE CASE
-> @timed @logged @retry(times=2) around an LLM call function
```

### 07 — Type Hints

[Full module →](07-type-hints/)


```text
TYPE HINTS
↓

def f(x: int) -> str: ...        class C(TypedDict):        Role = Literal["a", "b"]
x: list[str] = []                    field: int
y: int | None = None

Callable[[str], int]             TypeVar("T")                Annotated[int, "metadata"]

WHEN TO USE
-> documenting/statically checking function contracts and typed interfaces

COMMON MISTAKE
-> assuming a type hint validates untrusted data at runtime (it does not)

AI USE CASE
-> TypedDict + Literal for a typed tool-call/result contract between agent and tools
```

### 08 — Dataclasses

[Full module →](08-dataclasses/)


```text
DATACLASSES
↓

@dataclass                          @dataclass(frozen=True, slots=True)
class Point:                        class Immutable:
    x: float                            value: str
    y: float

field(default_factory=list)         # required for mutable defaults

WHEN TO USE
-> internal, trusted state you fully control (agent state, config, records)

COMMON MISTAKE
-> a bare mutable default (list/dict) instead of field(default_factory=...)

AI USE CASE
-> @dataclass(slots=True) class AgentState: goal: str; steps: list[Step] = field(default_factory=list)
```

### 09 — Pydantic

[Full module →](09-pydantic/)


```text
PYDANTIC
↓

class Model(BaseModel):              Field(ge=1, le=20)         @field_validator("field")
    field: str = Field(...)          Field(min_length=1)        @classmethod
                                                                 def check(cls, v): ...

Model.model_validate(data)   # parse + validate a dict
instance.model_dump()        # -> dict
instance.model_dump_json()   # -> JSON string

WHEN TO USE
-> validating untrusted data at a boundary (LLM output, API bodies, config)

COMMON MISTAKE
-> using a dataclass where the data actually needs runtime validation

AI USE CASE
-> ExtractedInvoice.model_validate(json.loads(llm_response))  # structured output
```

### 10 — Advanced OOP & Magic Methods

[Full module →](10-advanced-oop/)


```text
MAGIC METHODS
↓

__call__(self, *a, **kw)     obj(...)          callable tool/decorator objects
__get__/__set__               attribute access   reusable validated attributes (descriptors)
__set_name__                  descriptor setup    knows its own attribute name
__add__/__eq__/__repr__       +, ==, print()      operator overloading (use sparingly)
__iter__/__next__             for x in obj        see 02-iterators-generators
__aiter__/__anext__           async for x in obj  see 04-async-generators-streaming
__enter__/__exit__            with obj:           see 05-context-managers

WHEN TO USE
-> making a stateful object work with natural, expected Python syntax

COMMON MISTAKE
-> __eq__ raising instead of returning NotImplemented for an unrelated type

AI USE CASE
-> a callable Tool class: tool(**arguments) works like a function call but keeps state
```

### 11 — Protocols & Generics

[Full module →](11-protocols-generics/)


```text
PROTOCOLS & GENERICS
↓

class P(Protocol):              class Stack[T]:              class Repo[T: HasId]:
    def method(self) -> X: ...      def push(self, x: T): ...    def add(self, item: T): ...

@runtime_checkable        # enables isinstance() against a Protocol (name-only check)

WHEN TO USE
-> swappable provider/tool abstractions; generic containers reused across types

COMMON MISTAKE
-> assuming @runtime_checkable verifies method SIGNATURES (it only checks names exist)

AI USE CASE
-> class ModelProvider(Protocol): def generate(self, prompt: str) -> str: ...
   # swap real/local/fake providers with zero inheritance
```

### 12 — Concurrency

[Full module →](12-concurrency/)


```text
CONCURRENCY
↓

await asyncio.gather(*coros)              all results, original order, waits for all
for c in asyncio.as_completed(coros): ..  completion order, one at a time
asyncio.create_task(coro())               starts running immediately
async with asyncio.TaskGroup() as tg: ..  structured concurrency, auto-cancels siblings
async with asyncio.Semaphore(n): ...      caps concurrent work to n
async with asyncio.timeout(s): ...        bounds one await to s seconds

WHEN TO USE
-> fanning out many independent I/O-bound calls, safely bounded

COMMON MISTAKE
-> unbounded concurrent fan-out with no semaphore -> rate-limit bans, exhausted connections

AI USE CASE
-> semaphore + per-call timeout + per-call error handling around a batch of LLM calls
```

### 13 — HTTPX & Async HTTP

[Full module →](13-httpx-async-http/)


```text
HTTPX
↓

async with httpx.AsyncClient() as client:
    ...

response = await client.get(url)          GET request
response = await client.post(url, ...)     POST request
response.raise_for_status()                raise on 4xx/5xx
response.json()                            parse JSON body

httpx.Timeout(connect=1, read=5, write=5, pool=5)   explicit timeouts
httpx.AsyncClient(base_url="...")                    shared base URL

WHEN TO USE
-> one shared AsyncClient, reused for the lifetime of the app/request

COMMON MISTAKE
-> creating a new AsyncClient per request -- loses connection pooling

AI USE CASE
-> a small LLMClient class wrapping AsyncClient behind an async context manager
```

### 14 — Streaming: SSE & WebSockets

[Full module →](14-streaming-sse-websockets/)


```text
SSE & WEBSOCKETS
↓

StreamingResponse(gen(), media_type="text/event-stream")   SSE endpoint
yield f"data: {chunk}\n\n"                                  one SSE event

@app.websocket("/ws/path")                                  WebSocket endpoint
await websocket.accept()
await websocket.receive_text() / .send_text(...)            bidirectional messages

WHEN TO USE
-> SSE for one-way streaming; WebSocket for bidirectional/multi-turn sessions

COMMON MISTAKE
-> missing the blank-line event terminator in an SSE `data:` chunk

AI USE CASE
-> SSE for a single streamed LLM completion; WebSocket for a multi-turn agent chat
```

### 15 — Error Handling & Retries

[Full module →](15-error-handling-retries/)


```text
ERROR HANDLING & RETRIES
↓

class RetryableAPIError(Exception): ...       classify by TYPE
class NonRetryableAPIError(Exception): ...

delay = min(cap, base * 2**(attempt-1)) + jitter   exponential backoff + jitter

try:
    return await call()
except RetryableAPIError:
    if attempt == max_attempts: raise
    await asyncio.sleep(delay)
except NonRetryableAPIError:
    raise   # fail fast

CircuitBreaker: CLOSED -> OPEN (too many failures) -> HALF_OPEN (cooldown) -> CLOSED

WHEN TO USE
-> retry transient failures (429, 503, timeouts) with backoff; fail fast on the rest

COMMON MISTAKE
-> retrying a non-retryable error (bad auth, malformed request) -- it will never succeed

AI USE CASE
-> classify LLM API errors, back off on rate limits, fail fast on invalid prompts
```

### 16 — Caching

[Full module →](16-caching/)


```text
CACHING
↓

@functools.cache                    unbounded memoization
@functools.lru_cache(maxsize=128)   bounded, LRU-evicted memoization
f.cache_info() / f.cache_clear()    inspect / wipe

TTLCache.get_or_compute(key, fn)    expires after a fixed duration
VersionedCache.invalidate_all()     bump a version to invalidate everything at once

WHEN TO USE
-> repeated identical calls with a stable, well-defined key

COMMON MISTAKE
-> a cache key missing a parameter that actually changes the result

AI USE CASE
-> hash(model + temperature + prompt) as the LLM response cache key
```

### 17 — Queues & Background Tasks

[Full module →](17-queues-background-tasks/)


```text
QUEUES & BACKGROUND TASKS
↓

background_tasks.add_task(fn, *args)        fire-and-forget, after the response

queue = asyncio.Queue(maxsize=N)            bounded -- backpressure
await queue.put(item) / await queue.get()   producer / consumer
queue.task_done() / await queue.join()      mark done / wait for full drain

WHEN TO USE
-> slow work that shouldn't block a request; sustained job processing with a worker pool

COMMON MISTAKE
-> an unbounded queue with no backpressure -> unlimited memory growth under load

AI USE CASE
-> submit a document for embedding, return a job ID immediately, poll for the result
```

### 18 — Serialization

[Full module →](18-serialization/)


```text
SERIALIZATION
↓

json.dumps(data) / json.loads(text)         JSON-native types only
json.dumps(data, default=fn)                 handle datetime/bytes/custom types

Path("a") / "b.json"                         join paths
path.read_text() / path.write_text(text)     file I/O
path.exists() / .suffix / .stem / .parent    path inspection

model.model_dump_json()                      Pydantic: handles dates/enums automatically
Model.model_validate_json(text)              ...and validates on the way back in

WHEN TO USE
-> json for simple JSON-native data; Pydantic once dates/enums/nested models appear

COMMON MISTAKE
-> json.dumps(datetime.now()) -- TypeError, no built-in JSON rule for datetime

AI USE CASE
-> AgentState.model_validate_json(path.read_text())  # reload saved agent session state
```

### 19 — Testing with Pytest

[Full module →](19-testing-pytest/)


```text
TESTING WITH PYTEST
↓

def test_x(): assert ...                    a test
@pytest.fixture / yield ... teardown          reusable setup + teardown
@pytest.mark.asyncio  async def test_x(): ..  test async code directly
@pytest_asyncio.fixture  async def f(): ...   async fixture (NOT plain @pytest.fixture)
@pytest.mark.parametrize("x,exp", [...])      run one test body over many inputs
monkeypatch.setattr("module.fn", fake_fn)     temporarily replace something

WHEN TO USE
-> mocked HTTP/LLM calls in unit tests; real calls only in a separate integration suite

COMMON MISTAKE
-> a plain @pytest.fixture on an async generator -- needs @pytest_asyncio.fixture instead

AI USE CASE
-> httpx.MockTransport to fake an LLM API response inside an async test
```

### 20 — Logging & Observability

[Full module →](20-logging-observability/)


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

### 21 — Configuration & Environments

[Full module →](21-config-environments/)


```text
CONFIGURATION & ENVIRONMENTS
↓

os.environ["VAR"]              required, raises KeyError if missing
os.getenv("VAR", "default")    optional, with a fallback

load_dotenv(".env")            load a local .env file into the environment

class Settings(BaseSettings):  typed, validated, environment-sourced config
    api_key: SecretStr             required, masked in repr/logs
    temperature: float = 0.0       optional, type-coerced automatically

WHEN TO USE
-> any real service's configuration surface, especially anything secret or per-environment

COMMON MISTAKE
-> if os.getenv("DEBUG"): -- truthy for ANY non-empty string, including "false"

AI USE CASE
-> AIServiceSettings with a SecretStr API key and validated sampling parameters
```

### 22 — Dependency Injection

[Full module →](22-dependency-injection/)


```text
DEPENDENCY INJECTION
↓

class Service:                        manual constructor injection
    def __init__(self, dep): ...

class ModelProvider(Protocol): ...    typed interface (module 11)

def get_provider() -> ModelProvider:  FastAPI dependency function
    return RealProvider()

@app.get("/x")
def endpoint(p: ModelProvider = Depends(get_provider)): ...

app.dependency_overrides[get_provider] = lambda: FakeProvider()   test override
app.dependency_overrides.clear()                                   always clean up

WHEN TO USE
-> anything talking to an external/expensive/swappable service

COMMON MISTAKE
-> hardcoding a dependency internally instead of accepting it as a parameter

AI USE CASE
-> inject a ModelProvider so production uses the real API, tests use a fixed fake
```

### 23 — Packaging & Modern Python Tooling

[Full module →](23-packaging-modern-python/)


```text
PACKAGING & MODERN TOOLING
↓

pyproject.toml               single source of truth: metadata, deps, tool config
uv sync                       create .venv, install exactly what's declared
uv add <pkg> / --dev <pkg>    add a runtime / dev-only dependency
uv run <command>              run inside the project's managed environment
uv.lock                        exact, reproducible dependency versions

ruff check .                  lint (unused imports, likely bugs, style)
ruff check --fix .            auto-fix what's safely fixable
ruff format .                  consistent formatting, no manual effort

src/<package>/                the modern package layout

WHEN TO USE
-> any project with real dependencies -- reproducibility from day one

COMMON MISTAKE
-> no lockfile committed -> "works on my machine" across different resolved versions

AI USE CASE
-> the exact toolchain behind every module's requirements.txt in this repo, at project scale
```

### 24 — Performance & Memory

[Full module →](24-performance-memory/)


```text
PERFORMANCE & MEMORY
↓

a is b                  identity: same object?
a == b                  equality: same value?
id(a)                   the object's unique identifier

copy.copy(x)            shallow -- nested mutables still SHARED
copy.deepcopy(x)        deep -- fully independent, recursively

gc.collect()            force a cyclic-GC pass (cycles refcounting can't free)
weakref.ref(obj)        a reference that doesn't keep obj alive

cProfile.run("f()")     measure where time is ACTUALLY spent

WHEN TO USE deepcopy
-> forking/branching mutable state that must not be shared afterward

COMMON MISTAKE
-> a function silently mutating its caller's list/dict argument

AI USE CASE
-> deepcopy conversation state before branching into two independent agent paths
```

### 25 — GIL, Processes & Threads

[Full module →](25-gil-processes-threads/)


```text
GIL, PROCESSES & THREADS
↓

threading.Thread(target=fn, args=(...)).start() / .join()   I/O-bound only
multiprocessing.Pool(processes=N).map(fn, items)              CPU-bound, real parallelism

asyncio      -> I/O-bound, thousands of coroutines, single thread
threading    -> I/O-bound, blocking libraries with no async API
multiprocessing -> CPU-bound, genuine multi-core parallelism

WHEN TO USE
-> multiprocessing for CPU-bound work; asyncio/threading for I/O-bound work

COMMON MISTAKE
-> using threads to try to speed up pure-Python CPU-bound code (the GIL blocks this)

AI USE CASE
-> multiprocessing.Pool to parallelize a locally-run embedding/preprocessing batch
```

### 26 — Contextvars

[Full module →](26-contextvars/)


```text
CONTEXTVARS
↓

var = contextvars.ContextVar("name", default=...)   declare
token = var.set(value)                                set (returns a Token)
var.get()                                              read from anywhere downstream
var.reset(token)                                       restore the previous value

asyncio.Task creation -> copies the current Context    each task is isolated

WHEN TO USE
-> request-scoped state (request ID, current user) readable from deep, unpredictable call chains

COMMON MISTAKE
-> threading.local for async request context -- ALL tasks share one thread's storage

AI USE CASE
-> attribute every tool call/log line to the correct user across concurrent agent requests
```

### 27 — Production Python Patterns

[Full module →](27-production-python-patterns/)


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

### 28 — AI Engineering Patterns

[Full module →](28-ai-engineering-patterns/)


```text
AI ENGINEERING PATTERNS
↓

TOOL CALLING       model emits {name, args} -> validate args against a schema -> dispatch
STRUCTURED OUTPUT  model emits JSON -> Model.model_validate_json -> retry on ValidationError
STREAMING          chain small async-generator stages, each transforming the last
RAG                retrieve(query) -> augment_prompt(query, chunks) -> generate(prompt)
EVALUATION         fixed (input, expected) cases -> run pipeline -> pass rate, not vibes

WHEN TO USE
-> any LLM-driven system whose output triggers a real function, a record, or a shipped answer

COMMON MISTAKE
-> calling a tool/parsing a response without validating it against a schema first

AI USE CASE
-> this module IS the AI engineering use case -- these are the shapes real LLM/RAG/agent
   systems are built from
```

---

⬅ Back to [main README](README.md)
