# 13 — HTTPX & Async HTTP

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

Nearly every AI system call -- LLM API, vector DB, search API -- goes over HTTP. HTTPX's
async client is the standard tool for calling them concurrently, built directly on top of the
`async`/`await` and concurrency primitives from modules 03 and 12.

> Examples in this module need the `httpx` package. See [`requirements.txt`](requirements.txt).
> They use `httpx.MockTransport` (HTTPX's own testing tool) instead of real network calls, so
> they run offline and deterministically -- the client code itself is identical to what you'd
> write against a real API.

---

## 1. What is it?

HTTPX is an HTTP client library with both a synchronous (`httpx.Client`) and an asynchronous
(`httpx.AsyncClient`) API, sharing the same request/response interface. The async client
integrates with `asyncio`, so HTTP calls can be awaited and run concurrently like any other
coroutine.

## 2. Why does it exist?

```text
LLM application
 ├── LLM API
 ├── Search API
 └── Vector DB
```

Every one of those is a network call, and network calls are pure I/O wait -- exactly what
asyncio is built to overlap (module 03). `httpx.AsyncClient` is what actually lets you `await`
an HTTP request instead of blocking on it, and fan out many of them concurrently with
`asyncio.gather`.

## 3. 💡 Mental Model

```text
httpx.Client        -> blocks the thread until the response arrives
httpx.AsyncClient   -> awaits the response, letting the event loop do other work meanwhile
```

Same request-building API either way -- `.get()`, `.post()`, headers, JSON bodies -- the only
difference is whether you write `client.get(...)` or `await client.get(...)`.

## 4. Syntax

```python
import httpx

# Sync
with httpx.Client() as client:
    response = client.get("https://api.example.com/status")

# Async
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/status")
    response.raise_for_status()   # raises HTTPStatusError on 4xx/5xx
    data = response.json()

# Timeouts (connect/read/write/pool, configured once per client)
client = httpx.AsyncClient(timeout=httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=5.0))

# Concurrent calls through ONE shared client
results = await asyncio.gather(
    client.get("/a"), client.get("/b"), client.get("/c"),
)
```

## 5. Minimal Example

```python
import asyncio
import httpx

async def main() -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://httpbin.org/get")
        print(response.status_code)

asyncio.run(main())
```

## 6. What happens internally?

```text
async with httpx.AsyncClient() as client:
        │
        ▼
client opens a connection pool (no requests sent yet)
        │
        ▼
await client.get(url)
        │
        ▼
HTTPX builds the request, sends it over a pooled connection (reusing an
existing keep-alive connection if one to that host already exists),
and awaits the response -- yielding control to the event loop while
the network round-trip happens
        │
        ▼
on `async with` exit, the client closes its connection pool
```

## 7. Comparison: HTTPX Sync vs Async

| | `httpx.Client` | `httpx.AsyncClient` |
|---|---|---|
| Call style | `client.get(...)` | `await client.get(...)` |
| Blocks the thread while waiting? | yes | no -- yields to the event loop |
| Concurrent requests | needs threads | `asyncio.gather` on one shared client |
| Best for | simple scripts, sync codebases | web backends, concurrent API fan-out |
| AI use case | a one-off CLI script calling an API | a FastAPI backend calling an LLM concurrently with other services |

## 8. 🎯 AI Engineering Use Case

Wrapping `AsyncClient` in a small client class -- opened once via an async context manager,
reused for every request -- is the standard shape for talking to an LLM API from an AI
backend.

### Example A — Tiny

```python
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### Example B — Practical

```python
timeout = httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=5.0)
async with httpx.AsyncClient(timeout=timeout) as client:
    ...
```

### Example C — AI Engineering

```python
class LLMClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def __aenter__(self) -> "LLMClient":
        return self

    async def __aexit__(self, *exc) -> bool:
        await self._client.aclose()
        return False

    async def complete(self, prompt: str) -> str:
        response = await self._client.post("/v1/completions", content=prompt.encode())
        response.raise_for_status()
        return response.json()["completion"]
```

Full runnable version: [`examples/llm_api_client.py`](examples/llm_api_client.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
async with httpx.AsyncClient() as client:
    ...
✅ Use for:
- calling LLM/vector-DB/search APIs from async code (web backends, agents)
- fanning out multiple API calls concurrently

❌ Don't:
- create a brand-new client for every single request -- you lose connection
  pooling and pay setup/teardown cost repeatedly
- use the sync `httpx.Client` inside an `async def` function -- it blocks
  the event loop exactly like `time.sleep()` does (module 03)

BETTER ALTERNATIVE
Create one AsyncClient (or one per logical service) and reuse it for the
lifetime of your application/request handler.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — creating a new client per request instead of reusing one**

```python
# WRONG -- opens and tears down a fresh connection pool for every call,
# losing keep-alive reuse and adding setup overhead every time.
async def fetch(path: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com{path}")
        return response.json()
```

```python
# BETTER -- one client, reused across many calls
async def fetch_all(client: httpx.AsyncClient, paths: list[str]) -> list[dict]:
    responses = await asyncio.gather(*(client.get(p) for p in paths))
    return [r.json() for r in responses]
```

Runnable proof of the pattern: [`examples/client_reuse_and_pooling.py`](examples/client_reuse_and_pooling.py)

**Mistake 2 — forgetting `raise_for_status()` and silently processing an error response**

```python
# WRONG -- a 500 response still has a .json() body (maybe an error payload),
# so this happily "succeeds" while actually processing a failure.
response = await client.get(url)
data = response.json()
```

```python
# BETTER
response = await client.get(url)
response.raise_for_status()  # raises HTTPStatusError on 4xx/5xx
data = response.json()
```

**Mistake 3 — no timeout configured, relying on defaults blindly**

```python
# RISKY -- HTTPX does have sane default timeouts, but not configuring them
# explicitly means you don't actually know what they are for YOUR use case,
# and a slow LLM API can hold a connection open longer than acceptable.
client = httpx.AsyncClient()
```

```python
# BETTER -- configure timeouts explicitly for your actual latency budget
client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=1.0, read=10.0, write=10.0, pool=5.0)
)
```

Runnable proof of the resulting `httpx.TimeoutException`:
[`examples/timeouts_and_retries.py`](examples/timeouts_and_retries.py)

## 11. ⚡ Quick Tricks

```python
async with httpx.AsyncClient() as client:
    ...
```

```python
# Set a base_url once so every call only needs the path
client = httpx.AsyncClient(base_url="https://api.example.com")
await client.get("/status")  # -> https://api.example.com/status
```

```python
# Fan out multiple calls through one shared client
results = await asyncio.gather(*(client.get(p) for p in paths))
```

```python
# Test HTTP code with no real network at all
client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
```

## 12. Performance Considerations

- Connection pooling (keep-alive) is the entire reason to reuse a client -- each new
  `httpx.AsyncClient()` starts a fresh pool with no warmed-up connections, and TLS handshakes
  in particular are expensive to repeat.
- Batching independent calls through `asyncio.gather` on one shared client gets you both
  benefits at once: concurrency (module 12) and connection reuse (this module).

## 13. 🎤 Interview Questions

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

## 14. 🛠 Mini Exercise

Write an async function `fetch_json(client: httpx.AsyncClient, path: str) -> dict` that GETs
`path`, calls `raise_for_status()`, and returns the parsed JSON body -- then write
`fetch_all_json(client, paths: list[str]) -> list[dict]` that fetches multiple paths
concurrently using that helper.

<details>
<summary>Solution</summary>

```python
import asyncio
import httpx


async def fetch_json(client: httpx.AsyncClient, path: str) -> dict:
    response = await client.get(path)
    response.raise_for_status()
    return response.json()


async def fetch_all_json(client: httpx.AsyncClient, paths: list[str]) -> list[dict]:
    return await asyncio.gather(*(fetch_json(client, p) for p in paths))
```

</details>

## 15. Real-World Challenge

Extend [`examples/llm_api_client.py`](examples/llm_api_client.py)'s `LLMClient` with a
`stream_complete(prompt: str)` method using HTTPX's `client.stream()` API to iterate over
response bytes as they arrive, instead of waiting for the full body -- a preview of the
transport-level mechanics behind `14-streaming-sse-websockets`.

## 16. Cheat Sheet

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

---

⬅ Back to [main README](../README.md)
