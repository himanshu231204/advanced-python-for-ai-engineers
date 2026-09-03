# Interview Question Bank

Every "🎤 Interview Questions" section from every written module, in one page — a bank for
pre-interview review, organized in the same order as the curriculum. Each entry links back
to its full module for the underlying explanation and runnable examples.

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


**Q: Why is `def f(items=[]):` considered dangerous?**
A: The default list is created once when the function is defined, not each call. Every
invocation that doesn't pass its own `items` shares and mutates that same list, so state
leaks across unrelated calls. Fix: default to `None` and create the list inside the function.

**Q: What's the difference between `*args` and `**kwargs`?**
A: `*args` collects extra **positional** arguments into a tuple; `**kwargs` collects extra
**keyword** arguments into a dict. Both let a function accept an open-ended set of inputs,
which is exactly what a generic tool dispatcher or decorator wrapper needs.

**Q: What does a keyword-only parameter (`def f(a, *, b):`) buy you?**
A: It forces callers to pass `b` by name, which makes call sites self-documenting and
prevents accidental positional misordering -- important once a function has more than 2-3
parameters, like `create_agent(*, name, model, temperature)`.

**Q: What is a closure, and where would you actually use one in an AI system?**
A: A closure is a function that captures variables from its enclosing scope, even after
that scope has returned. Used for rate limiters, memoized caches, and configuration-baked
callbacks (e.g. `make_retry(max_attempts=3)` returning a ready-to-use retry function).


### 02 — Iterators & Generators

[Full module →](02-iterators-generators/)


**Q: What's the difference between an iterable and an iterator?**
A: An iterable is anything `iter()` can be called on (lists, generators, custom objects
implementing `__iter__`). An iterator is the stateful object that actually produces values via
`__next__()`. Every iterator is iterable (its `__iter__` returns itself), but not every
iterable is an iterator (a list is iterable but isn't itself an iterator).

**Q: Generator vs list — when would memory usage differ, and by how much?**
A: A list holds every element in memory simultaneously; a generator holds only its current
position and local state. For a million computed values, a list might use megabytes while a
generator uses a couple hundred bytes -- the difference grows with the size of the sequence,
not with anything about the generator itself.

**Q: What does `yield from` actually do?**
A: It delegates iteration to a sub-iterable, re-yielding each of its values as if the outer
generator had yielded them directly -- equivalent to (but more efficient and correct than)
manually writing `for x in sub_iterable: yield x`, and it also correctly forwards `send()`,
`throw()`, and the sub-generator's return value.

**Q: Why can't you call `next()` on a generator twice and get the same value?**
A: A generator's execution state is mutated by each `next()` call -- it resumes past the
`yield` it stopped at and runs until the next one. There's no way to "rewind" without creating
a brand-new generator from scratch.


### 03 — Asyncio Fundamentals

[Full module →](03-asyncio/)


**Q: Why doesn't asyncio automatically make CPU-bound Python faster?**
A: asyncio achieves concurrency by yielding control at `await` points while something else
(I/O) is happening. A CPU-bound function has no I/O to wait on -- it never yields -- so it
occupies the single event-loop thread from start to finish, exactly like a normal blocking
function call. True CPU parallelism needs multiple OS processes (`multiprocessing`), which
sidestep the GIL.

**Q: What happens when you forget `await`?**
A: The coroutine function call returns a coroutine object instead of running the function
body. No error is raised at the call site, but you get a `RuntimeWarning: coroutine '...' was
never awaited`, and any code relying on the (missing) return value silently breaks.

**Q: What's the difference between a coroutine and a Task?**
A: A coroutine is a paused computation that does nothing until awaited or scheduled. A Task
(created via `asyncio.create_task` or implicitly by `asyncio.gather`) wraps a coroutine and
schedules it to run on the event loop independently -- it starts making progress even before
you `await` it, which is what enables true concurrency between multiple coroutines.

**Q: Why is calling `time.sleep()` inside an `async def` function considered a serious bug in
a server context?**
A: It blocks the entire event loop's single thread for that duration, so every other
in-flight coroutine (every other user's request, in a web server) is frozen too -- not just
the one function that called it.


### 04 — Async Generators & Streaming

[Full module →](04-async-generators-streaming/)


**Q: How would you stream an LLM response using an async generator?**
A: Write an `async def` function that `yield`s each token (or chunk) as it's produced,
`await`-ing the underlying network read between yields instead of blocking. A consumer (e.g.
a FastAPI endpoint) then does `async for chunk in stream: write(chunk)`, sending each piece to
the client immediately rather than waiting for the full response.

**Q: Why can't a regular generator use `await`?**
A: `yield` and `await` are different suspension mechanisms tied to different underlying
protocols (`__next__` vs the awaitable protocol driven by the event loop). A plain `def`
function's frame has no way to hand control to the event loop; only inside `async def` does
Python make that machinery available, which is why async generators require `async def` +
`yield` together.

**Q: What's backpressure, and why does it matter for streaming pipelines?**
A: Backpressure is a mechanism that slows a fast producer down to match a slower consumer,
usually via a bounded buffer (like `asyncio.Queue(maxsize=...)`) that blocks the producer once
full. Without it, a fast producer and slow consumer combination leads to unbounded memory
growth as unconsumed items pile up.

**Q: What exception does `async for` rely on to know a stream has ended?**
A: `StopAsyncIteration`, raised (implicitly, when the function body returns) by the async
generator's `__anext__` -- the async counterpart of `StopIteration` in module 02.


### 05 — Context Managers

[Full module →](05-context-managers/)


**Q: What guarantee does a context manager actually give you?**
A: That `__exit__` (or `__aexit__`) runs once the block is entered, regardless of whether the
block completes normally, returns early, or raises an exception -- equivalent to a `finally`
block, but reusable and attached to the resource itself instead of duplicated at every call
site.

**Q: What does it mean if `__exit__` returns `True`?**
A: Any exception raised inside the `with` block is suppressed -- it will not propagate past
the `with` statement. Returning `False` (or `None`, the default) lets the exception propagate
normally after `__exit__` finishes running.

**Q: Why do async context managers need separate `__aenter__`/`__aexit__` methods instead of
just `__enter__`/`__exit__`?**
A: `__enter__`/`__exit__` are plain synchronous methods -- they cannot contain `await`.
Anything that needs to perform async I/O during setup or teardown (an async connection
handshake, an async close call) needs the `async def __aenter__`/`__aexit__` methods that
`async with` specifically looks for.

**Q: When would you choose a class-based context manager over `@contextmanager`?**
A: When the object needs other methods beyond just enter/exit (e.g. a client with `.get()`,
`.post()`, etc. in addition to being used as a context manager), or when the setup/teardown
state is complex enough that instance attributes are clearer than closure variables in a
generator function.


### 06 — Decorators

[Full module →](06-decorators/)


**Q: What does `@decorator` actually do under the hood?**
A: It's syntax sugar for `func = decorator(func)`, executed once when the module is loaded --
not once per call. Whatever `decorator` returns becomes the new value bound to `func`'s name.

**Q: Why is `functools.wraps` important?**
A: Without it, the decorated function's `__name__`, `__doc__`, and other metadata are replaced
by the wrapper function's own -- this breaks debugging output, documentation generation, and
any code that introspects the function (e.g. some routing/registration systems keyed on
function name).

**Q: How would you write a decorator that itself takes arguments, like `@retry(times=3)`?**
A: Add an extra level of nesting: an outer function (`retry`) that takes the configuration
arguments and returns the actual decorator function, which in turn takes `fn` and returns the
wrapper. `retry(times=3)` first runs and returns a decorator, which is then applied to the
function.

**Q: If you stack `@a` then `@b` above a function, which one runs first when the function is
called?**
A: `@b` (the one closest to the `def`) wraps the original function first, and `@a` wraps
*that* result. So execution order at call time is: `a`'s pre-call code, then `b`'s pre-call
code, then the original function, then `b`'s post-call code, then `a`'s post-call code.


### 07 — Type Hints

[Full module →](07-type-hints/)


**Q: Do Python type hints get enforced at runtime?**
A: No. Python stores them (in `__annotations__`) but never checks them during normal
execution. Enforcement comes from a separate static analysis tool (mypy, pyright) run
separately, typically in CI or an editor -- or from a library like Pydantic that explicitly
performs runtime validation using type hints as its schema.

**Q: Why use Pydantic instead of plain dictionaries (or TypedDict) for LLM structured
output?**
A: A `TypedDict` only provides *static* shape-checking -- it does nothing at runtime, so
malformed LLM output (a missing field, wrong type) would silently corrupt your data or crash
somewhere downstream. Pydantic actively validates every field when the object is constructed,
raising a clear error immediately if the LLM's output doesn't match the expected shape.

**Q: What's the difference between `TypeVar` and `Generic`?**
A: `TypeVar` declares a placeholder type variable used to link related types across a
function's or class's signature (e.g. "the input list and the returned single item are the
same type `T`"). `Generic` is the base class a *class* inherits from to become
parameterizable by one or more `TypeVar`s (e.g. `class Box(Generic[T])`). Full depth on both
is in `11-protocols-generics`.

**Q: What does `Literal["a", "b"]` buy you over just typing something as `str`?**
A: It narrows the type to a specific, enumerable set of allowed values, so a type checker can
catch a typo or an invalid value (like `"moderator"` where only `"system"`, `"user"`, or
`"assistant"` are valid) at check time -- a plain `str` would accept literally anything.


### 08 — Dataclasses

[Full module →](08-dataclasses/)


**Q: Does `@dataclass` validate the types declared in its annotations?**
A: No. Type hints on a dataclass are purely for static analysis (mypy/pyright) and for
generating `__init__`'s signature -- nothing checks at runtime that a `float` field actually
received a `float`. Use Pydantic when you need that guarantee.

**Q: Why can't you write `history: list[str] = []` directly in a dataclass?**
A: Because it's the exact mutable-default-argument bug from module 01 -- the empty list would
be created once, at class definition time, and shared across every instance that doesn't
override it. Dataclasses actively detect this for common mutable types and raise a
`ValueError` at class-definition time rather than let the bug happen silently; the fix is
`field(default_factory=list)`, which calls `list()` fresh for each new instance.

**Q: What does `frozen=True` actually guarantee?**
A: That any attempt to set an attribute on an instance after `__init__` raises
`FrozenInstanceError`. Combined with the default `eq=True`, frozen dataclasses also become
hashable, so they can be used as dict keys or set members -- something a normal mutable
dataclass cannot do safely.

**Q: When would you choose a dataclass over a Pydantic model?**
A: When the data is internal and fully trusted -- you construct every instance yourself and
control exactly what values go in, so there's no need to pay Pydantic's validation cost or
pull in the dependency. Once the data originates outside your code (an LLM's structured
output, a request body), Pydantic's validation becomes worth its cost.


### 09 — Pydantic

[Full module →](09-pydantic/)


**Q: Why use Pydantic instead of plain dictionaries for LLM structured output?**
A: A plain dict gives you no guarantee about its shape -- a missing key or wrong type only
surfaces later, wherever the code first tries to use it incorrectly, with a confusing error
far from the actual cause. Pydantic validates the entire shape immediately when the data
arrives, raising one clear error naming every problem, right at the boundary where the
untrusted data entered.

**Q: What's the practical difference between a dataclass and a Pydantic model?**
A: A dataclass generates `__init__`/`__repr__`/`__eq__` from annotations but performs zero
runtime validation -- it will happily store a `str` in a field annotated `int`. A Pydantic
model uses the same annotations to actually validate (and where safe, coerce) every field at
construction time, raising `ValidationError` on a mismatch.

**Q: What exception does Pydantic raise on invalid data, and what does it contain?**
A: `pydantic.ValidationError`. Calling `.errors()` on it returns a list of every failing
field (not just the first), each with a `loc` (the field path, useful for nested models) and
a `msg` describing exactly what went wrong.

**Q: When would a dataclass be the better choice over Pydantic, even in an AI system?**
A: For internal state you construct yourself and fully control -- agent run state, an
intermediate pipeline result -- where there's no untrusted boundary being crossed. Paying
Pydantic's validation cost there buys you nothing, since the data was never at risk of being
malformed in the first place.


### 10 — Advanced OOP & Magic Methods

[Full module →](10-advanced-oop/)


**Q: What's the difference between `__repr__` and `__str__`?**
A: `__repr__` is meant for developers -- ideally unambiguous enough to help debugging, often
written to look like valid Python that could reconstruct the object. `__str__` is meant for
end users and is what `print()` and `str()` use if defined; if `__str__` is missing, Python
falls back to `__repr__`.

**Q: Why should `__eq__` return `NotImplemented` instead of `False` for an incompatible
type?**
A: Returning `NotImplemented` tells Python "I don't know how to compare these -- try the
other object's `__eq__`, or fall back to identity comparison" rather than asserting a
definite (and possibly wrong) answer. Returning `False` directly would incorrectly claim two
objects of totally different types are known to be unequal by this class's logic, even when
this class has no idea how to compare them.

**Q: What problem do descriptors solve that `@property` doesn't?**
A: `@property` defines get/set logic for one specific attribute on one specific class.
Descriptors let you write that logic ONCE, in a separate reusable class, and attach it to
many different attributes across many different classes -- exactly like the `PositiveNumber`
descriptor being reused for any "must be positive" attribute.

**Q: How does `obj()` actually dispatch to `__call__`?**
A: Python looks up `__call__` on `type(obj)` (the class), not on the instance itself, and
calls it as `type(obj).__call__(obj, ...)`. This is true of all dunder methods, which is why
assigning `__call__` directly onto an instance has no effect on whether that instance is
callable.


### 11 — Protocols & Generics

[Full module →](11-protocols-generics/)


**Q: What's the difference between structural typing (`Protocol`) and nominal typing
(inheritance/ABC)?**
A: Nominal typing checks whether a class explicitly declares itself part of a type's family
(via inheritance). Structural typing checks whether an object simply *has* the right
shape (methods/attributes) -- Python calls this "duck typing," and `Protocol` makes it
checkable by static tools without requiring any inheritance relationship.

**Q: Why would you use `Protocol` instead of an abstract base class for a model-provider
abstraction?**
A: Because different LLM SDKs are third-party classes you don't control -- you can't make
`OpenAIClient` inherit from your own `ModelProvider` ABC. A `Protocol` lets any of those
classes satisfy your abstraction automatically, as long as they have a compatible method,
with zero changes to the SDK's own code.

**Q: What does `@runtime_checkable` actually check, and what does it NOT check?**
A: It lets `isinstance()`/`issubclass()` be used against a Protocol, checking that the object
has attributes/methods with the required *names*. It does **not** check method signatures
(parameter types, return types) -- a method with the right name but a completely wrong
signature still passes the `isinstance()` check.

**Q: What's a bounded TypeVar, and why would a generic class need one?**
A: A bounded type parameter (`class Repository[T: HasId]`) restricts what concrete types `T`
can be to those satisfying some constraint (here, having an `id` attribute). This lets the
generic class's body safely use `item.id` for any valid `T`, because a type checker
guarantees every substitution satisfies that bound.


### 12 — Concurrency

[Full module →](12-concurrency/)


**Q: How would you limit 1000 concurrent API calls to at most 20 at a time?**
A: Wrap each call in `async with semaphore:` where `semaphore = asyncio.Semaphore(20)`, then
`asyncio.gather` all 1000 wrapped coroutines. The semaphore blocks the 21st coroutine's
`async with` block from proceeding until one of the first 20 releases its permit, so at most
20 calls are ever actually in flight.

**Q: What's the difference between `asyncio.gather` and `asyncio.as_completed`?**
A: `gather` waits for every coroutine and returns all results together, in the original
argument order. `as_completed` returns an iterator that yields each coroutine's result as
soon as it finishes, in completion order -- useful when you want to react to the fastest
result without waiting for the slowest.

**Q: Why prefer `asyncio.TaskGroup` over manually managing a list of tasks?**
A: `TaskGroup` provides structured concurrency: if any task in the group raises, the others
are automatically cancelled and the group itself raises an `ExceptionGroup` you can handle
with `except*`. Manually tracking tasks requires writing that cancellation and error-
aggregation logic yourself, and it's easy to leak a task that never gets cancelled.

**Q: What happens to the other 99 concurrent calls if one of 100 gathered coroutines raises
an exception, using default `asyncio.gather` settings?**
A: By default, `gather` immediately propagates the first exception it sees and cancels the
remaining tasks -- so you lose the results (or in-progress work) of every other call unless
you either catch exceptions inside each coroutine, or pass `return_exceptions=True` to have
`gather` return exceptions as regular result values instead of raising.


### 13 — HTTPX & Async HTTP

[Full module →](13-httpx-async-http/)


**Q: Why should you reuse one `httpx.AsyncClient` instead of creating a new one per
request?**
A: Each client manages its own connection pool. Reusing one client lets HTTPX keep
connections alive and reuse them across requests to the same host, avoiding the cost of a
fresh TCP (and, for HTTPS, TLS) handshake on every single call.

**Q: What's the practical difference between `httpx.Client` and `httpx.AsyncClient` for an
AI backend?**
A: `httpx.Client` blocks the calling thread for the full duration of each request. Inside an
`async def` handler (e.g. FastAPI), that would block the entire event loop -- exactly like
calling `time.sleep()` in async code (module 03). `httpx.AsyncClient` awaits instead, letting
the event loop serve other requests while waiting on the network.

**Q: What does `response.raise_for_status()` do, and why call it explicitly?**
A: It raises `httpx.HTTPStatusError` if the response status code is 4xx or 5xx. Without
calling it, a failed request (e.g. a 500 from an overloaded LLM API) still returns a
`Response` object you can call `.json()` on -- silently treating an error response as if it
were a valid result unless you check the status yourself.

**Q: How would you call three independent APIs (an LLM, a vector DB, a search API)
concurrently with HTTPX?**
A: Create one `httpx.AsyncClient`, build a coroutine for each call (`client.get(...)` /
`client.post(...)`), and pass all three to `asyncio.gather`. This starts all three requests
essentially at once and returns once every one has completed, taking roughly as long as the
slowest single call rather than the sum of all three.


### 14 — Streaming: SSE & WebSockets

[Full module →](14-streaming-sse-websockets/)


**Q: How would you stream an LLM response to a frontend?**
A: Wrap the async generator producing tokens (module 04) in a FastAPI `StreamingResponse`
with `media_type="text/event-stream"`, formatting each token as an SSE `data: ...\n\n` chunk.
The browser's `EventSource` (or any SSE client) then receives and renders each token as it
arrives, instead of waiting for the full response.

**Q: SSE vs WebSocket -- how do you decide?**
A: If the server only ever needs to push data to the client (a single completion, progress
updates, notifications), SSE is simpler: it's plain HTTP, works through most
proxies/load balancers without special handling, and reconnects automatically. If the client
also needs to send new messages while the connection is open (an ongoing chat/agent session),
that requires a WebSocket's bidirectional channel.

**Q: What does the blank line in an SSE event actually do?**
A: It's the event delimiter -- everything before it (one or more `data:`/`event:`/`id:`
lines) is one event; the blank line tells the client "this event is complete, start parsing
the next one." Omitting it means a client can't reliably tell where one event ends and the
next begins.

**Q: Why can't a single HTTP request/response handle a multi-turn agent chat the way a
WebSocket can?**
A: An HTTP request/response is inherently one-shot: the client sends one request, the server
sends one response (even if that response is streamed), and the connection is done. A new
user message would require an entirely new HTTP request, losing the ability to keep sending
new client messages on the same already-open connection the way a WebSocket allows.


### 15 — Error Handling & Retries

[Full module →](15-error-handling-retries/)


**Q: How do you decide whether an error is retryable?**
A: By its type/status code, not by guessing from context. Rate limits (429), timeouts, and
5xx server errors are typically transient and worth retrying. Client errors like 400
(malformed request) or 401 (bad credentials) will fail identically every time, since retrying
sends the exact same broken request again -- those should fail fast instead.

**Q: Why use exponential backoff instead of a fixed delay between retries?**
A: A fixed short delay can still overwhelm a struggling service with rapid repeated attempts.
Exponential backoff gives the service progressively more time to recover between attempts,
and adding jitter (a small random amount) prevents many clients from retrying in lockstep at
the exact same intervals, which would otherwise create synchronized traffic spikes.

**Q: What problem does a circuit breaker solve that retries with backoff don't?**
A: Retries handle a single caller's individual failed request. A circuit breaker protects
against a fully-down dependency: once failures cross a threshold, it stops attempting calls
entirely for a cooldown period, sparing both the caller (no more wasted timeouts) and the
downstream service (no more load while it's trying to recover).

**Q: Why is retrying a non-idempotent operation (like a payment charge) risky?**
A: If the original request actually succeeded server-side but the response was lost (e.g. a
network timeout after the charge went through), blindly retrying could duplicate the side
effect -- charging twice. Safe retries for non-idempotent operations need an idempotency key
so the server can recognize and ignore a duplicate retry of the same logical request.


### 16 — Caching

[Full module →](16-caching/)


**Q: What's the difference between caching and memoization?**
A: Memoization is a specific technique: caching a function's return value keyed by its exact
arguments, so calling it again with the same arguments returns the stored result instantly.
Caching is the broader concept -- storing any expensive result under any meaningful key, not
necessarily tied to a function's arguments (e.g. caching an HTTP response by URL, or an LLM
response by a hash of its prompt and parameters).

**Q: Why doesn't `functools.lru_cache` support expiration?**
A: It's designed purely around a bounded-size, recency-based eviction policy (Least Recently
Used) -- not time. If entries need to expire after a fixed duration, you need a TTL-aware
cache built on top of (or instead of) `lru_cache`, tracking an expiry timestamp alongside
each cached value.

**Q: What must a cache key for an LLM response include, and why?**
A: Everything that can change the model's output: the prompt, the model name/version, and any
sampling parameters (temperature, top_p, etc.). Omitting any of these risks serving a cached
response that doesn't actually correspond to the request being made -- a subtle correctness
bug, not just a performance one.

**Q: When would caching an LLM response be a bad idea?**
A: When high variability in output is actually desired (e.g. creative generation at high
temperature, where the whole point is a different answer each time), or when the underlying
context changes so quickly that a cached answer would likely be wrong by the time it's served.


### 17 — Queues & Background Tasks

[Full module →](17-queues-background-tasks/)


**Q: When would you use FastAPI's `BackgroundTasks` instead of a full task queue?**
A: For quick, low-stakes work tied to a single request's lifecycle -- logging, sending a
notification -- where losing the task on a crash is an acceptable risk and no cross-process
coordination is needed. Anything that must survive a restart, be retried reliably, or run on
a different machine than the web server needs a real task queue instead.

**Q: Why use a bounded queue instead of an unbounded one for background job processing?**
A: An unbounded queue lets a producer that's faster than the consumers pile up unlimited
in-memory work, risking out-of-memory failures under sustained load. A bounded queue makes
`put()` block (apply backpressure) once full, capping memory use at the cost of slowing the
producer down to match actual processing capacity.

**Q: How would you let a client check on a long-running background job's progress?**
A: Generate a job ID when the job is submitted, store its status (pending/running/done/
failed) and eventual result keyed by that ID, and expose a separate endpoint the client can
poll with the job ID to retrieve the current status -- exactly the submit/poll pattern used
for batch embedding or long-running agent runs.

**Q: What's the risk of relying only on in-process `BackgroundTasks` for critical work?**
A: If the process crashes or restarts after the response is sent but before the background
task finishes (or even starts), that work is silently lost -- there's no persistence, retry,
or cross-process visibility. Critical work needs a durable task queue that survives process
restarts.


### 18 — Serialization

[Full module →](18-serialization/)


**Q: Why does `json.dumps(datetime.now())` raise an error?**
A: The `json` module's encoder only knows how to serialize a fixed set of JSON-native Python
types (dict, list, str, int, float, bool, None). `datetime` isn't one of them, so without an
explicit conversion (either manually, via `.isoformat()`, or via a `default=` function), the
encoder has no rule for turning it into JSON and raises `TypeError`.

**Q: Why does a plain `Enum` fail to serialize with `json.dumps`, but a `str, Enum` mixin
works?**
A: `json` checks the actual runtime type of each value. A plain `Enum` member's type is the
Enum class itself, not `str`, so it's not JSON-native. A class that inherits from both `str`
and `Enum` produces members that genuinely *are* strings at runtime (in addition to being
Enum members), so `json` serializes them exactly like any other string.

**Q: What advantage does `pathlib.Path` have over building paths with string concatenation
or `os.path.join`?**
A: `Path` objects handle platform-specific separators correctly (`/` vs `\`) via the `/`
operator itself, provide convenient properties (`.suffix`, `.stem`, `.parent`) without manual
string parsing, and offer methods like `.read_text()`/`.write_text()`/`.exists()` directly on
the path object instead of needing separate `open()`/`os.path.exists()` calls.

**Q: Why would you use Pydantic's `model_dump_json`/`model_validate_json` instead of the raw
`json` module for saving agent state to disk?**
A: Agent state typically includes rich types like timestamps and role enums that the `json`
module can't serialize without custom handling. Pydantic handles those automatically, AND
validates the data's shape again on load -- catching corruption or format drift in a saved
file instead of silently loading malformed data.


### 19 — Testing with Pytest

[Full module →](19-testing-pytest/)


**Q: What's the difference between a fixture and a regular helper function in pytest?**
A: A fixture is registered with pytest and automatically injected into any test (or other
fixture) that declares it as a parameter by name -- pytest resolves and calls it for you,
supports `yield`-based teardown, and can be scoped (per-test, per-module, per-session). A
plain helper function has to be called explicitly inside each test and has no built-in
teardown mechanism.

**Q: How would you test an `async def` function with pytest?**
A: Install `pytest-asyncio`, mark the test function `async def` and decorate it with
`@pytest.mark.asyncio`, then `await` the code under test directly inside the test body --
pytest-asyncio handles running the test inside an event loop.

**Q: Why mock an LLM API call in a test instead of calling the real API?**
A: Real API calls are slow, can fail for reasons unrelated to the code being tested (network
issues, rate limits), cost money, and produce non-deterministic output -- all of which make
tests flaky and expensive to run frequently. Mocking (e.g. with `httpx.MockTransport`) makes
the test fast, deterministic, and free, while still exercising the actual request/response
handling code.

**Q: What does `@pytest.mark.parametrize` actually do, and what happens if you stack two of
them on the same test?**
A: It runs the same test function once per entry in the given list of argument values,
reporting each as a separate test result. Stacking two `@parametrize` decorators runs the
test once for every *combination* of both lists (the full cross product), not just once per
list.


### 20 — Logging & Observability

[Full module →](20-logging-observability/)


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


### 21 — Configuration & Environments

[Full module →](21-config-environments/)


**Q: Why should API keys and other secrets never be hardcoded in source code?**
A: Hardcoded secrets get committed to version control, remaining visible in git history even
after being "removed" later, and are exposed to anyone with repository access. Reading them
from the environment (backed by a secrets manager or a gitignored `.env` file in local dev)
keeps the actual secret value out of the codebase entirely.

**Q: What's a common bug with treating environment variables as booleans?**
A: `os.getenv("DEBUG")` returns a string or `None` -- never an actual `bool`. Code like `if
os.getenv("DEBUG"):` is truthy for any non-empty string, including `"false"` or `"0"`, which
silently does the opposite of what's intended. The fix is either explicit string comparison
(`.lower() == "true"`) or a typed settings library that parses booleans correctly.

**Q: What does `pydantic_settings.BaseSettings` give you over plain `os.getenv` calls?**
A: The same type coercion and validation as a regular Pydantic model (module 09), applied to
environment variables specifically -- required fields raise a clear error if missing, types
are automatically converted from strings, and (with `SecretStr`) sensitive values are masked
in any repr or log output.

**Q: How would you structure configuration to safely differ between development and
production?**
A: Use one `Settings` shape (so the code always accesses the same typed fields) with an
`environment` field selecting which actual values apply -- either via different `.env`
files/environment variables per deployment, or explicit per-environment override logic --
rather than scattering `if environment == "production":` checks throughout the codebase.


### 22 — Dependency Injection

[Full module →](22-dependency-injection/)


**Q: What problem does dependency injection solve?**
A: It decouples a piece of code from the concrete implementations it relies on, letting the
caller supply whichever implementation is appropriate -- the real service in production, a
fast deterministic fake in tests -- without changing the dependent code itself.

**Q: How does FastAPI's `Depends` system work under the hood?**
A: A dependency is just a callable. When FastAPI sees `param: T = Depends(some_callable)` on
an endpoint's signature, it calls `some_callable()` (or looks up an override registered in
`app.dependency_overrides`) for each incoming request, and passes the result as that
parameter's value.

**Q: Why depend on a `Protocol` (interface) rather than a concrete class?**
A: Depending on a concrete class ties the code to that specific implementation's shape,
forcing any fake/test double to literally subclass it. Depending on a `Protocol` lets any
object with a compatible shape satisfy the dependency, real or fake, without any inheritance
relationship required.

**Q: What's a risk of using `app.dependency_overrides` carelessly in a test suite?**
A: If an override isn't cleared after the test that set it, it can leak into subsequent
tests (or, in a badly structured test harness, even affect real usage), silently causing
unrelated tests to run against a fake dependency instead of the real one they expected.


### 23 — Packaging & Modern Python Tooling

[Full module →](23-packaging-modern-python/)


**Q: What problem does `pyproject.toml` solve that the old `setup.py`/`requirements.txt`
combination didn't?**
A: It consolidates project metadata, dependencies, build configuration, and tool settings
into one standardized, declarative file instead of scattering them across multiple files with
inconsistent formats -- making projects easier to understand, more consistent across tools,
and less error-prone to maintain.

**Q: What does a lockfile (`uv.lock`) actually guarantee that `pyproject.toml` alone doesn't?**
A: `pyproject.toml` typically declares dependency *ranges* (e.g. `httpx>=0.27`); a lockfile
pins the exact resolved versions of every dependency (and transitive dependency) that were
installed. `uv sync` using the lockfile reproduces the identical environment every time,
rather than potentially resolving to different (but technically compatible) versions on
different machines or at different times.

**Q: What does Ruff replace, and why is that consolidation useful?**
A: Ruff combines the functionality of several older tools -- flake8 (linting), isort (import
sorting), and largely Black (formatting) -- into one fast tool with one configuration section
in `pyproject.toml`, instead of maintaining separate configs and separate slow tool
invocations for each.

**Q: Why put a package's source code under `src/` instead of directly at the project root?**
A: The `src/` layout prevents accidentally importing the package via a stray current-
directory `sys.path` entry instead of the actually-installed version -- forcing tests (and
any other code) to only see the package if it's genuinely installed (even in editable mode),
which catches packaging mistakes that a flat layout can hide.


### 24 — Performance & Memory

[Full module →](24-performance-memory/)


**Q: Generator vs list -- when would memory usage differ? (a recap tying back to module 02)**
A: A list materializes every element in memory at once; a generator holds only its current
position and local state, producing values lazily. For a large or unbounded sequence, a
generator can use orders of magnitude less memory -- the same underlying reference/object
model applies to both, but a generator simply never creates most of the objects a list would.

**Q: Why doesn't reference counting alone free a reference cycle?**
A: Reference counting frees an object the instant its count reaches zero. In a cycle (A
refers to B, B refers back to A), each object is still referenced by the other, so neither
count ever reaches zero, even once nothing outside the cycle refers to either of them. A
separate cyclic garbage collector is needed to detect and free such unreachable cycles.

**Q: What's the difference between `is` and `==`?**
A: `is` checks object identity -- whether two references point to the exact same object in
memory. `==` checks equality, which can be true for two distinct objects with the same
value (e.g. two separate list objects both containing `[1, 2, 3]`).

**Q: Why would you deep-copy conversation/agent state before branching it?**
A: Branching means both the original and the new branch need to be mutated independently
going forward. A shallow copy only duplicates the outermost container -- nested mutable
structures (like a message list) remain shared, so mutating one branch would silently
corrupt the other. A deep copy makes the branches genuinely independent.


### 25 — GIL, Processes & Threads

[Full module →](25-gil-processes-threads/)


**Q: Why doesn't asyncio automatically make CPU-bound Python faster?**
A: asyncio achieves concurrency by yielding control at `await` points while waiting on I/O.
A CPU-bound task has nothing to wait on -- it never yields -- so it runs to completion on the
single event-loop thread, exactly like ordinary blocking code. There's no parallelism to gain
from asyncio for CPU-bound work; that requires actual OS-level parallelism (separate
processes).

**Q: What does the GIL actually prevent?**
A: It prevents more than one thread from executing Python bytecode at the same time within
one process, even on a multi-core machine. It does NOT prevent threads from running
concurrently while blocked on I/O -- the GIL is released during blocking calls, which is why
threading still helps I/O-bound work.

**Q: Why does `multiprocessing` avoid the GIL problem that `threading` has?**
A: Each process spawned by `multiprocessing` has its own separate Python interpreter, its own
memory space, and therefore its own GIL. Since there's no shared interpreter state between
processes, multiple processes can genuinely execute Python bytecode simultaneously across
different CPU cores.

**Q: When would you choose threading over multiprocessing for I/O-bound work, given asyncio
also exists?**
A: When working with a library that only offers a blocking (non-async) API and provides no
async alternative -- threading lets you run that blocking call without freezing your whole
program, without the heavier overhead multiprocessing would add for a purely I/O-bound task.


### 26 — Contextvars

[Full module →](26-contextvars/)


**Q: Why can't you use a plain global variable for request-scoped state in an async web
backend?**
A: A plain global is shared by every concurrently-running task on the event loop. If two
requests are being handled "at the same time" (interleaved on one thread, as asyncio does),
one request's write to the global would be visible to (and could corrupt) another's read.

**Q: Why does `threading.local` fail to solve this problem under asyncio, even though it
solves the analogous problem for real multi-threaded code?**
A: `threading.local` isolates storage per OS *thread*. asyncio runs all of its tasks on a
single thread, so every task shares the exact same `threading.local` storage -- there's no
per-task isolation, only per-thread, which doesn't help when everything is on one thread.

**Q: What does a `Task` actually copy when contextvars are involved?**
A: When an `asyncio.Task` is created, it copies the *current context* -- a snapshot of every
`ContextVar`'s current value at that moment. Changes made to a `ContextVar` inside that task
only affect its own copy, and are invisible to sibling tasks or to whatever created the task.

**Q: When would you choose an explicit function parameter over a `ContextVar`?**
A: When the value is only needed a call or two deep, or when explicitness genuinely aids
readability -- forcing every reader to know "this value comes from ambient context" has a
real cost. `ContextVar` earns its keep specifically when a value needs to reach arbitrarily
deep, unpredictable call chains (logging, tracing) without threading it through every
signature along the way.


### 27 — Production Python Patterns

[Full module →](27-production-python-patterns/)


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


### 28 — AI Engineering Patterns

[Full module →](28-ai-engineering-patterns/)


**Q: Why validate a model's tool-call arguments instead of calling the function directly with
them?**
A: The model can emit malformed or wrongly-typed arguments (a string where an int is
expected, a missing required field). Validating against a schema first turns that into one
clear, catchable error at the dispatch boundary instead of an arbitrary exception deep inside
the tool's own code.

**Q: What's the benefit of splitting a streaming pipeline into separate async generator
stages instead of one function that does everything?**
A: Each stage becomes independently testable and replaceable -- the accumulator or the
sentence-splitter can be swapped or unit tested without needing a real token source, and the
same accumulator stage can be reused in a pipeline that ends differently.

**Q: Why keep retrieve, augment, and generate as three separate functions in a RAG
pipeline?**
A: It lets each piece be replaced independently -- swap the retriever for a real vector DB,
or the generator for a different LLM provider, without touching the orchestration logic that
wires them together, and lets each be unit tested with the other two mocked out.

**Q: Why does an evaluation harness need a fixed set of (input, expected) cases instead of
manually checking a few outputs?**
A: Manual spot-checks aren't repeatable or comparable -- there's no way to tell if a prompt
or model change made things better or worse. A fixed case set with a pass rate gives a single
number to compare across changes.


---

⬅ Back to [main README](README.md)
