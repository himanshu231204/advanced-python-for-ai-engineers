# 19 — Testing with Pytest

**Level:** 2 (Production Python) | **Status:** ✅ Written

Testing async code, mocked LLM calls, and streaming responses needs patterns beyond basic
pytest -- this module covers what production AI services actually test: fixtures,
`pytest-asyncio`, mocking HTTP/LLM calls, testing generators, and parametrized tests.

> Examples in this module need `pytest`, `pytest-asyncio`, and `httpx`. See
> [`requirements.txt`](requirements.txt). Every example here IS a pytest test file --
> "running" it means `python3 -m pytest <file>.py -v`, not `python3 <file>.py`.

---

## 1. What is it?

Pytest is Python's most widely used testing framework: a test is just a function named
`test_*` using plain `assert`, with **fixtures** providing reusable setup/teardown that tests
request as parameters. Extensions like `pytest-asyncio` add support for testing `async def`
code directly.

## 2. Why does it exist?

Manually verifying that a retry function actually retries, that a token stream yields the
right sequence, or that an LLM client handles a 500 response correctly, doesn't scale as a
codebase grows. Automated tests catch regressions the moment they're introduced, and pytest's
fixtures/parametrization keep test code itself from becoming as messy as the thing it tests.

## 3. 💡 Mental Model

```text
test function      -> just a function; assert failures are what pytest reports as failures
fixture             -> reusable setup/teardown, requested by name as a test's parameter
@pytest.mark.asyncio -> lets a test function itself be `async def`
@pytest.mark.parametrize -> runs ONE test body against MANY input/output pairs
```

## 4. Syntax

```python
import pytest

def test_add():
    assert add(2, 3) == 5

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_uses_fixture(sample_data):
    assert sample_data["key"] == "value"

@pytest.fixture
def resource_with_teardown():
    resource = open_resource()
    yield resource          # setup runs before yield
    resource.close()        # teardown runs after the test, pass or fail

@pytest.mark.asyncio
async def test_async_code():
    result = await my_coroutine()
    assert result == expected

@pytest.mark.parametrize("input,expected", [(1, 2), (2, 4), (3, 6)])
def test_doubling(input, expected):
    assert double(input) == expected
```

## 5. Minimal Example

```python
def add(a: int, b: int) -> int:
    return a + b

def test_add():
    assert add(2, 3) == 5
```

## 6. What happens internally?

```text
python3 -m pytest test_file.py
        │
        ▼
pytest discovers every function named test_* in the file
        │
        ▼
for each test, it inspects the function's PARAMETERS -- any name matching
a known fixture gets that fixture's return value automatically injected
        │
        ▼
runs the test body; an AssertionError (from a failed `assert`) or any
other exception is reported as a failure -- no exception means it passed
        │
        ▼
after the test, any fixture that used `yield` runs its teardown code
```

## 7. Comparison: Fixture vs Parametrize vs Monkeypatch

| | Fixture | `@pytest.mark.parametrize` | `monkeypatch` |
|---|---|---|---|
| Purpose | reusable setup/teardown | run one test body against many inputs | temporarily replace an attribute/function |
| Scope | injected per test that requests it | applies to the decorated test only | automatically undone after the test |
| AI use case | a reusable mocked HTTP client | testing a retry classifier against many status codes | swapping a real LLM call for a fake during a test |

## 8. 🎯 AI Engineering Use Case

Testing an LLM-calling function without ever hitting a real (slow, billable, flaky) API is
essential -- `httpx.MockTransport` (module 13) fakes the HTTP layer entirely inside the test.

### Example A — Tiny

```python
def test_add():
    assert add(2, 3) == 5
```

### Example B — Practical

```python
@pytest.mark.parametrize("status_code, expected", [(429, True), (200, False)])
def test_is_retryable(status_code, expected):
    assert is_retryable(status_code) is expected
```

### Example C — AI Engineering

```python
@pytest.mark.asyncio
async def test_call_llm_with_mock_transport():
    def handler(request):
        prompt = request.read().decode()
        return httpx.Response(200, json={"completion": f"response to: {prompt}"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await call_llm(client, "hello")

    assert result == "response to: hello"
```

Full runnable version: [`examples/test_mocking_llm_calls.py`](examples/test_mocking_llm_calls.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
PYTEST FIXTURES & MOCKING
✅ Good for:
- reusable setup shared across many tests (a mocked client, sample data)
- testing async code and generators without hand-rolling an event loop
- verifying behavior across many inputs at once (parametrize)

❌ Avoid when:
- a test genuinely needs to hit a real, live API (rare -- usually reserved
  for a small, separate suite of integration/smoke tests, run deliberately)
- over-mocking so much that the test no longer verifies anything real
  about the code's actual behavior

BETTER ALTERNATIVE
Reserve real network calls for a clearly separate integration test suite,
run less frequently than the fast, fully-mocked unit test suite.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — using a plain `@pytest.fixture` for an async fixture**

```python
# WRONG -- pytest doesn't natively understand an async generator fixture
# decorated with the plain @pytest.fixture; it errors at test setup.
@pytest.fixture
async def async_resource():
    yield {"ready": True}
```

```python
# BETTER -- async fixtures need @pytest_asyncio.fixture
import pytest_asyncio

@pytest_asyncio.fixture
async def async_resource():
    yield {"ready": True}
```

Runnable proof of the exact error and the fix: [`examples/test_async_pytest.py`](examples/test_async_pytest.py)

**Mistake 2 — a test that actually hits a real network endpoint**

```python
# WRONG -- slow, flaky (depends on network/API availability), and can
# cost real money against a billed LLM API, every single test run.
async def test_llm_call():
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.real-llm-provider.com/v1/completions", ...)
```

```python
# BETTER -- fake the HTTP layer entirely with httpx.MockTransport
async def test_llm_call():
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        ...
```

**Mistake 3 — forgetting a generator is exhausted after one pass, in a test**

```python
# WRONG -- asserting on the same generator object twice; the second
# assertion silently checks against an empty result, not a bug in the code.
gen = countdown(2)
assert list(gen) == [2, 1]
assert list(gen) == [2, 1]  # FAILS -- gen is already exhausted, this is [] now
```

```python
# BETTER -- create a fresh generator for each assertion that needs to
# consume it from the start
assert list(countdown(2)) == [2, 1]
assert list(countdown(2)) == [2, 1]
```

Runnable proof: [`examples/test_generators.py`](examples/test_generators.py)

## 11. ⚡ Quick Tricks

```python
# Fixture with teardown
@pytest.fixture
def resource():
    r = setup()
    yield r
    teardown(r)
```

```python
# Test many cases with one test body
@pytest.mark.parametrize("x,expected", [(1, 2), (2, 4)])
def test_double(x, expected):
    assert double(x) == expected
```

```python
# Temporarily replace a function for one test, auto-restored after
def test_something(monkeypatch):
    monkeypatch.setattr("module.function_name", fake_function)
```

```python
# Consume an async generator fully inside a test
tokens = [t async for t in stream_tokens(text)]
```

## 12. Performance Considerations

- Mocking external calls (rather than hitting real services) is what keeps a test suite fast
  enough to run on every commit -- a suite that makes real network calls quickly becomes too
  slow (and flaky) to run frequently.
- Parametrized tests multiply run count (stacking two `@parametrize` decorators produces the
  full cross product) -- keep parameter lists focused on genuinely distinct cases, not
  exhaustive combinations that add runtime without adding real coverage.

## 13. 🎤 Interview Questions

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

## 14. 🛠 Mini Exercise

Write a pytest fixture `sample_messages()` returning a list of three dict messages (each with
`role` and `content` keys), and a parametrized test `test_role_is_valid` that checks each
message's `role` is one of `"system"`, `"user"`, `"assistant"` using
`@pytest.mark.parametrize` over the fixture's contents (hint: you can parametrize directly
over a literal list without needing the fixture, or use the fixture inside a non-parametrized
test that loops -- pick whichever is clearer).

<details>
<summary>Solution</summary>

```python
import pytest

VALID_ROLES = {"system", "user", "assistant"}


@pytest.fixture
def sample_messages() -> list[dict]:
    return [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]


def test_all_roles_are_valid(sample_messages: list[dict]) -> None:
    for message in sample_messages:
        assert message["role"] in VALID_ROLES
```

</details>

## 15. Real-World Challenge

Extend [`examples/test_mocking_llm_calls.py`](examples/test_mocking_llm_calls.py) with a
parametrized test that feeds `call_llm` several different mock HTTP status codes (200, 429,
500) via a handler that varies its response, asserting `raise_for_status()` correctly raises
for the error codes and succeeds for 200 -- combining mocking, async tests, and
parametrization from this whole module into one test.

## 16. Cheat Sheet

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

---

⬅ Back to [main README](../README.md)
