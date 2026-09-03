# 22 — Dependency Injection

**Level:** 2 (Production Python) | **Status:** ✅ Written

Typed service interfaces and DI make it possible to swap an LLM provider, vector DB, or tool
implementation without touching business logic. This module combines module 11's `Protocol`
pattern with the actual injection mechanics -- both by hand and via FastAPI's built-in
`Depends` system.

> `fastapi_depends_basics.py`, `testing_with_fakes.py`, and `swappable_llm_provider.py` need
> `fastapi` and `httpx` -- see [`requirements.txt`](requirements.txt).

---

## 1. What is it?

Dependency injection means a piece of code receives its dependencies from the outside
(a constructor parameter, a function argument) instead of creating or hardcoding them
internally. FastAPI's `Depends` is a built-in mechanism for this: declare a dependency
function, and FastAPI calls it and passes the result into any endpoint that asks for it.

## 2. Why does it exist?

```text
Python Concept
      ↓
Protocol (interface)
      ↓
Dependency Injection
      ↓
swap real/fake implementations with zero changes to business logic
```

A class that hardcodes `self.client = RealAPIClient()` can never be tested without hitting
the real API, and can never be pointed at a different implementation without editing its
source. Injecting the dependency instead means the *caller* decides what implementation to
use -- production code gets the real thing, tests get a fast, deterministic fake.

## 3. 💡 Mental Model

```text
WITHOUT injection: class creates its OWN dependency internally
    class Service:
        def __init__(self):
            self.client = RealClient()   # hardcoded -- can't be swapped

WITH injection: dependency is passed IN
    class Service:
        def __init__(self, client):     # caller decides what `client` is
            self.client = client
```

## 4. Syntax

```python
# DI without a framework -- just a constructor parameter
class Service:
    def __init__(self, dependency: SomeProtocol) -> None:
        self._dependency = dependency

# Typed interface (module 11) -- so ANY compatible implementation works
class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

# FastAPI's Depends -- the framework's own DI mechanism
from fastapi import Depends, FastAPI

def get_model_provider() -> ModelProvider:
    return OpenAIStyleProvider()

@app.get("/generate")
def generate(prompt: str, provider: ModelProvider = Depends(get_model_provider)):
    return {"result": provider.generate(prompt)}

# Testing with an injected fake
app.dependency_overrides[get_model_provider] = lambda: FakeModelProvider()
```

## 5. Minimal Example

```python
class Service:
    def __init__(self, dependency) -> None:
        self._dependency = dependency

    def run(self) -> str:
        return self._dependency.do_work()

class FakeDependency:
    def do_work(self) -> str:
        return "fake result"

Service(FakeDependency()).run()  # "fake result" -- no real dependency needed
```

## 6. What happens internally?

```text
@app.get("/generate")
def generate(prompt: str, provider: ModelProvider = Depends(get_model_provider)):
    ...
        │
        ▼
when a request hits this endpoint, FastAPI sees the `Depends(get_model_provider)`
default value on the `provider` parameter
        │
        ▼
it calls get_model_provider() (or looks up an override in
app.dependency_overrides if one is set for THIS callable)
        │
        ▼
the return value is passed in as the `provider` argument -- the endpoint
function itself never calls get_model_provider() directly
```

## 7. Comparison: Manual DI vs FastAPI `Depends`

| | Manual DI (constructor injection) | FastAPI `Depends` |
|---|---|---|
| Where dependencies are wired | wherever you construct the object | declared per-endpoint, resolved by the framework |
| Swapping for tests | pass a different argument | `app.dependency_overrides[fn] = lambda: fake` |
| Works outside a web framework? | yes -- pure Python | tied to FastAPI's request lifecycle |
| AI use case | a service class taking an injected `ModelProvider` | an endpoint taking an injected `ModelProvider` |

## 8. 🎯 AI Engineering Use Case

An endpoint that depends on a `ModelProvider` interface (not a concrete class) can have its
real implementation swapped for a fixed, fast fake in tests -- with zero changes to the
endpoint's own code.

### Example A — Tiny

```python
class Service:
    def __init__(self, dependency) -> None:
        self._dependency = dependency
```

### Example B — Practical

```python
def get_settings() -> Settings:
    return Settings()

@app.get("/config")
def read_config(settings: Settings = Depends(get_settings)):
    return {"model_name": settings.model_name}
```

### Example C — AI Engineering

```python
class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

def get_model_provider() -> ModelProvider:
    return OpenAIStyleProvider()

@app.get("/generate")
def generate(prompt: str, provider: ModelProvider = Depends(get_model_provider)):
    return {"result": provider.generate(prompt)}

# In tests:
app.dependency_overrides[get_model_provider] = lambda: FakeModelProvider()
```

Full runnable version: [`examples/swappable_llm_provider.py`](examples/swappable_llm_provider.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
DEPENDENCY INJECTION
✅ Good for:
- anything that talks to an external service (LLM API, vector DB, database)
  where tests should never hit the real thing
- code that needs to support multiple implementations (different LLM
  providers, different storage backends)

❌ Avoid when:
- a dependency is truly a fixed, stateless utility with no reasonable
  alternative implementation (injecting `math.sqrt` gains nothing)
- it adds indirection to code that will only ever have one implementation
  and is trivial to construct directly

BETTER ALTERNATIVE
For simple, stateless helpers, just call them directly. Reserve DI for
dependencies that are expensive, external, or genuinely need to vary
between production and tests.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — hardcoding a dependency instead of injecting it**

```python
# WRONG -- this class can NEVER be tested without a real email service,
# and can never be pointed at a different sender implementation.
class NotificationService:
    def __init__(self) -> None:
        self._sender = RealEmailSender()
```

```python
# BETTER -- accept the dependency as a parameter
class NotificationService:
    def __init__(self, sender: EmailSender) -> None:
        self._sender = sender
```

Runnable proof: [`examples/di_without_framework.py`](examples/di_without_framework.py)

**Mistake 2 — forgetting to clear a `dependency_overrides` after a test**

```python
# WRONG -- an override left in place leaks into OTHER tests (or even
# production, if this ever runs outside a proper test fixture/teardown),
# silently using a fake where the real dependency was expected.
app.dependency_overrides[get_model_provider] = lambda: FakeModelProvider()
# ...test runs...
# (forgot to clear it)
```

```python
# BETTER -- always clear overrides once the test is done (ideally in a
# fixture's teardown, so it happens even if the test fails)
app.dependency_overrides[get_model_provider] = lambda: FakeModelProvider()
try:
    ...  # run the test
finally:
    app.dependency_overrides.clear()
```

**Mistake 3 — depending on a concrete class instead of an interface**

```python
# WRONG -- depending on the concrete OpenAIStyleProvider class means a
# fake used in tests must actually SUBCLASS it, coupling tests to
# production implementation details unnecessarily.
def generate(prompt: str, provider: OpenAIStyleProvider = Depends(get_model_provider)):
    ...
```

```python
# BETTER -- depend on the Protocol; any compatible object works, real or fake
def generate(prompt: str, provider: ModelProvider = Depends(get_model_provider)):
    ...
```

Runnable proof: [`examples/typed_service_interface.py`](examples/typed_service_interface.py)

## 11. ⚡ Quick Tricks

```python
# Constructor injection -- the simplest form of DI, no framework needed
def __init__(self, dependency: SomeProtocol) -> None:
    self._dependency = dependency
```

```python
# FastAPI dependency function
def get_settings() -> Settings:
    return Settings()
```

```python
# Override a dependency for tests
app.dependency_overrides[get_settings] = lambda: Settings(debug=True)
```

```python
# Always clear overrides afterward
app.dependency_overrides.clear()
```

## 12. Performance Considerations

- FastAPI calls a dependency function fresh on every request by default -- for something
  expensive to construct (a real API client with connection pooling), consider constructing
  it once at startup and having the dependency function just return the shared instance,
  rather than rebuilding it per request.
- Manual constructor injection has effectively zero runtime overhead -- it's just passing an
  argument.

## 13. 🎤 Interview Questions

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

## 14. 🛠 Mini Exercise

Write a `Clock` protocol with a `now() -> float` method, a `RealClock` implementation using
`time.monotonic()`, and a function `measure(clock: Clock, fn) -> float` that returns how long
`fn()` took to run, using the injected clock instead of calling `time.monotonic()` directly
-- so a test can inject a `FakeClock` with fully controlled, deterministic timings.

<details>
<summary>Solution</summary>

```python
import time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float: ...


class RealClock:
    def now(self) -> float:
        return time.monotonic()


class FakeClock:
    def __init__(self, values: list[float]) -> None:
        self._values = iter(values)

    def now(self) -> float:
        return next(self._values)


def measure(clock: Clock, fn) -> float:
    start = clock.now()
    fn()
    return clock.now() - start


measure(RealClock(), lambda: time.sleep(0.01))  # a real, small elapsed time

fake = FakeClock([0.0, 2.5])  # first call to now() returns 0.0, second returns 2.5
print(measure(fake, lambda: None))  # 2.5 -- fully deterministic, no real timing involved
```

</details>

## 15. Real-World Challenge

Extend [`examples/swappable_llm_provider.py`](examples/swappable_llm_provider.py) with a
second dependency, `get_rate_limiter`, injected alongside `get_model_provider` into the same
endpoint, and override both simultaneously in a test -- practice composing multiple injected
dependencies on one endpoint, which is the normal shape of a real production route.

## 16. Cheat Sheet

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

---

⬅ Back to [main README](../README.md)
