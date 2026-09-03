# 16 — Caching

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

Caching repeated LLM calls, embeddings, and tool results cuts both latency and cost -- but
only when you cache the right thing for the right lifetime, with a key that actually captures
everything that affects the result.

---

## 1. What is it?

Caching stores the result of an expensive operation so a later request for the same thing can
be served instantly instead of redone. **Memoization** is the specific case of caching a
function's return value, keyed by its exact arguments -- `functools.cache`/`lru_cache` are
Python's built-in memoization decorators.

## 2. Why does it exist?

An LLM call is slow and costs money every single time, even for an identical prompt asked
twice. If the same input reliably produces the same (or an acceptably reusable) output,
computing it once and serving the cached result for repeat requests saves both latency and
cost -- as long as the cache key and lifetime are chosen correctly.

## 3. 💡 Mental Model

```text
cache vs memoization
↓
memoization = caching a FUNCTION's output, keyed by its arguments
caching     = the broader idea -- any stored result, keyed by anything
              meaningful (a prompt hash, a URL, a document ID)
```

## 4. Syntax

```python
from functools import cache, lru_cache

@cache                    # unbounded -- keeps every distinct key forever
def f(x: int) -> int: ...

@lru_cache(maxsize=128)   # bounded -- evicts the Least Recently Used entry
def g(x: int) -> int: ...

f.cache_info()   # CacheInfo(hits=, misses=, maxsize=, currsize=)
f.cache_clear()  # wipe the cache

# TTL cache (functools has no built-in expiry -- roll your own or use a library)
import time

class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[object, tuple[float, object]] = {}

    def get_or_compute(self, key, compute):
        now = time.monotonic()
        if key in self._store and now < self._store[key][0]:
            return self._store[key][1]
        value = compute()
        self._store[key] = (now + self.ttl_seconds, value)
        return value
```

## 5. Minimal Example

```python
from functools import cache

@cache
def square(n: int) -> int:
    print(f"computing square({n})")
    return n * n

square(4)  # prints "computing square(4)", returns 16
square(4)  # cache hit -- no print, returns 16 instantly
```

## 6. What happens internally?

```text
@cache
def f(x): ...

f(4)
        │
        ▼
build a cache key from the arguments (here, just `(4,)`)
        │
        ▼
key NOT in the cache dict -> call the real function, store the result
under that key, return it
        │
        ▼
f(4) again
        │
        ▼
key IS in the cache dict -> return the stored result immediately,
the function body never runs
```

## 7. Comparison: Cache vs Memoization

| | Memoization (`functools.cache`) | General caching (custom key/store) |
|---|---|---|
| Key | the function's exact arguments | anything meaningful (prompt hash, URL, doc ID) |
| Expiry | never (unbounded) or LRU eviction (bounded) | you control it -- TTL, versioning, manual |
| Requires hashable args? | yes -- a `TypeError` otherwise | no -- you design the key |
| AI use case | memoizing a pure local function | caching LLM responses, embeddings, API results |

## 8. 🎯 AI Engineering Use Case

Caching LLM responses requires a key that captures *everything* that affects the output --
the prompt, the model, and any sampling parameters -- so two genuinely different requests
never collide on the same cached (wrong) answer.

### Example A — Tiny

```python
@cache
def square(n: int) -> int:
    return n * n
```

### Example B — Practical

```python
class TTLCache:
    def get_or_compute(self, key, compute):
        ...  # returns the cached value if still fresh, else recomputes
```

### Example C — AI Engineering

```python
def cache_key(prompt: str, *, model: str, temperature: float) -> str:
    raw = f"{model}|{temperature}|{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()

class LLMCache:
    def get_or_call(self, prompt, *, model, temperature):
        key = cache_key(prompt, model=model, temperature=temperature)
        ...  # TTL-based lookup, falling back to the real LLM call
```

Full runnable version: [`examples/llm_response_cache.py`](examples/llm_response_cache.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
CACHING
✅ Good for:
- repeated identical LLM prompts/parameters (deterministic or low-temperature)
- embeddings for content that rarely changes
- expensive, pure computations with a small, stable input space

❌ Avoid when:
- the underlying data changes frequently and staleness is unacceptable
- the "same" input can legitimately produce different valid outputs every
  time (high-temperature sampling where variety is the point)
- the cache key would need to include so much context that cache hits
  become rare anyway

BETTER ALTERNATIVE
For frequently-changing or highly variable data, skip caching (or use a
very short TTL) rather than serving confidently wrong stale results.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — a cache key missing a parameter that affects the result**

```python
# WRONG -- keying only on the prompt means a temperature=0.7 request can
# be served a cached temperature=0.0 response, or vice versa.
def cache_key(prompt: str) -> str:
    return prompt
```

```python
# BETTER -- include every parameter that changes the output
def cache_key(prompt: str, *, model: str, temperature: float) -> str:
    return f"{model}|{temperature}|{prompt}"
```

Runnable proof different temperatures produce different cache entries:
[`examples/llm_response_cache.py`](examples/llm_response_cache.py)

**Mistake 2 — expecting `functools.cache` to expire entries**

```python
# WRONG ASSUMPTION -- @cache never expires anything on its own; a stale
# result (e.g. from before a config change) is served forever until the
# process restarts or .cache_clear() is called manually.
@cache
def get_config(key: str) -> str: ...
```

```python
# BETTER -- use a TTL cache for anything that can go stale
cache = TTLCache(ttl_seconds=300)
value = cache.get_or_compute(key, lambda: get_config(key))
```

Runnable proof: [`examples/ttl_cache.py`](examples/ttl_cache.py)

**Mistake 3 — trying to memoize a function with unhashable arguments**

```python
# WRONG -- functools.cache needs every argument to be hashable; a list
# raises TypeError, even though the code "looks" fine.
@cache
def process(items: list[str]) -> int:
    return len(items)

process(["a", "b"])  # TypeError: unhashable type: 'list'
```

```python
# BETTER -- convert to a hashable type (tuple) before calling, or accept
# a tuple in the function's own signature.
@cache
def process(items: tuple[str, ...]) -> int:
    return len(items)

process(("a", "b"))
```

Runnable proof: [`examples/cache_vs_memoization.py`](examples/cache_vs_memoization.py)

## 11. ⚡ Quick Tricks

```python
from functools import cache
@cache
def f(x): ...
```

```python
# See exactly how well a cache is performing
f.cache_info()  # CacheInfo(hits=.., misses=.., maxsize=.., currsize=..)
```

```python
# Invalidate everything at once with a version bump instead of hunting
# down individual stale keys
self._version += 1
```

```python
# Build a safe cache key from multiple parameters with a hash
hashlib.sha256(f"{a}|{b}|{c}".encode()).hexdigest()
```

## 12. Performance Considerations

- `functools.cache` (unbounded) can grow forever if called with unlimited distinct arguments
  -- use `lru_cache(maxsize=N)` for anything with a large or unbounded input space, to cap
  memory use.
- The whole point of caching is trading memory for latency -- measure that the hit rate is
  actually high enough to be worth it; a cache with a near-0% hit rate just adds overhead.

## 13. 🎤 Interview Questions

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

## 14. 🛠 Mini Exercise

Write a decorator `ttl_cache(seconds: float)` that memoizes a function's results for a fixed
duration, re-computing once that duration has elapsed for a given set of arguments (hint:
store `(expires_at, result)` per argument tuple, similar to the `TTLCache` class but as a
decorator instead of a class with a method).

<details>
<summary>Solution</summary>

```python
import time
import functools


def ttl_cache(seconds: float):
    def decorator(fn):
        store: dict[tuple, tuple[float, object]] = {}

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            if key in store and now < store[key][0]:
                return store[key][1]
            result = fn(*args, **kwargs)
            store[key] = (now + seconds, result)
            return result

        return wrapper

    return decorator


calls = {"n": 0}


@ttl_cache(seconds=0.2)
def slow(x: int) -> int:
    calls["n"] += 1
    return x * 2


print(slow(3), calls["n"])  # 6 1
print(slow(3), calls["n"])  # 6 1 -- cached
time.sleep(0.25)
print(slow(3), calls["n"])  # 6 2 -- recomputed after TTL expired
```

</details>

## 15. Real-World Challenge

Extend [`examples/llm_response_cache.py`](examples/llm_response_cache.py)'s `LLMCache` with a
maximum entry count, evicting the oldest entry (by insertion or expiry time) once the limit is
exceeded -- combining this module's TTL idea with `lru_cache`'s size-bounding idea into one
cache.

## 16. Cheat Sheet

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

---

⬅ Back to [main README](../README.md)
