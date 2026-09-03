# 15 — Error Handling & Retries

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

LLM APIs fail, rate-limit, and time out. Knowing what's retryable -- and how to back off
correctly -- is the difference between a resilient system and a cascading outage. This module
builds the actual decision-making and backoff logic that earlier modules (12's concurrency,
13's HTTPX timeouts) pointed toward but deliberately left for here.

---

## 1. What is it?

A set of patterns for handling failure in calls to unreliable external services: classifying
errors as retryable or not, backing off between retries so you don't hammer a struggling
service, and circuit breakers that stop trying entirely once a service is clearly down.

## 2. Why does it exist?

Not every failure means the same thing. A rate limit (429) means "try again shortly." A bad
API key (401) means "this will never work no matter how many times you retry." Treating every
failure the same way -- always retry, or never retry -- either wastes time hammering a
permanently broken request, or gives up too early on a transient blip that would have
succeeded on the next attempt.

## 3. 💡 Mental Model

```text
Retry flow:

  call fails
      │
      ▼
  is it retryable?  ──NO──> fail fast, surface the real error immediately
      │
     YES
      │
      ▼
  attempts left?  ──NO──> raise (all retries exhausted)
      │
     YES
      │
      ▼
  wait (exponential backoff + jitter), then retry
```

## 4. Syntax

```python
# Exception hierarchy -- classify errors by TYPE, not by parsing messages
class APIError(Exception): pass
class RetryableAPIError(APIError): pass       # 429, 503, timeouts
class NonRetryableAPIError(APIError): pass    # 400, 401, malformed request

# Exponential backoff with jitter
import random

def backoff_delay(attempt: int, *, base: float = 0.1, cap: float = 5.0) -> float:
    exponential = min(cap, base * (2 ** (attempt - 1)))
    return exponential + random.uniform(0, exponential * 0.5)

# Retry loop
for attempt in range(1, max_attempts + 1):
    try:
        return await call()
    except RetryableAPIError:
        if attempt == max_attempts:
            raise
        await asyncio.sleep(backoff_delay(attempt))
    except NonRetryableAPIError:
        raise  # fail fast -- retrying won't help
```

## 5. Minimal Example

```python
class RetryableError(Exception):
    pass

def call_with_retry(fn, *, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except RetryableError:
            if attempt == max_attempts:
                raise
```

## 6. What happens internally?

```text
call_with_retry(flaky_fn, max_attempts=3)
        │
        ▼
attempt 1: flaky_fn() raises RetryableError -> attempts left, so continue
        │
        ▼
backoff_delay(1) computed, sleep, then attempt 2
        │
        ▼
attempt 2: flaky_fn() raises again -> attempts left, continue
        │
        ▼
backoff_delay(2) (roughly double attempt 1's delay), sleep, then attempt 3
        │
        ▼
attempt 3: flaky_fn() succeeds -> return the result immediately
   (if attempt 3 had ALSO failed, the exception re-raises here since
   max_attempts was reached)
```

## 7. Comparison: Retry vs Circuit Breaker vs Fail-Fast

| | Retry (with backoff) | Circuit breaker | Fail-fast |
|---|---|---|---|
| Purpose | recover from a transient failure | stop hammering a service that's clearly down | never waste time on a doomed request |
| When it triggers | on each individual retryable failure | after N consecutive failures | on any non-retryable error |
| Protects | the caller's own success rate | the struggling downstream service AND the caller's latency | the caller's time/resources |
| AI use case | a single rate-limited LLM call | an LLM provider having an outage | a malformed request (bad auth, invalid prompt) |

## 8. 🎯 AI Engineering Use Case

A production LLM call needs all three: classify the failure to decide retryable vs not, back
off with jitter between retries, and fail fast immediately on anything retrying can't fix.

### Example A — Tiny

```python
class RetryableError(Exception):
    pass
```

### Example B — Practical

```python
def backoff_delay(attempt: int, *, base=0.1, cap=5.0) -> float:
    exponential = min(cap, base * (2 ** (attempt - 1)))
    return exponential + random.uniform(0, exponential * 0.5)
```

### Example C — AI Engineering

```python
async def call_llm_with_retry(prompt: str, *, max_attempts: int = 5) -> str:
    for attempt in range(1, max_attempts + 1):
        try:
            return await call_llm(prompt)
        except RateLimitError:
            if attempt == max_attempts:
                raise
            await asyncio.sleep(backoff_delay(attempt))
        except InvalidPromptError:
            raise  # fail fast -- the prompt itself is broken
```

Full runnable version: [`examples/llm_retry_with_backoff.py`](examples/llm_retry_with_backoff.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
RETRIES WITH BACKOFF
✅ Good for:
- transient failures: rate limits, timeouts, temporary server overload
- calls where a short delay genuinely improves the odds of success

❌ Avoid when:
- the error is NEVER going to resolve by retrying (bad auth, malformed
  request, a 404) -- fail fast instead
- retries could cause duplicate side effects (e.g. a non-idempotent write)
  without an idempotency key to make the retry safe

BETTER ALTERNATIVE
Add a circuit breaker in front of retries for services that can go
fully down -- it stops the retry loop itself from becoming part of the
problem (piling up timeouts against a dead service).
```

## 10. 🚨 Common Mistakes

**Mistake 1 — retrying non-retryable errors**

```python
# WRONG -- retrying a 401 (bad credentials) five times just delays
# surfacing a real, unfixable configuration problem.
for attempt in range(5):
    try:
        return call_api()
    except Exception:
        continue  # retries EVERYTHING, including auth/validation failures
```

```python
# BETTER -- classify first, only retry what's actually retryable
try:
    return call_api()
except RetryableAPIError:
    ...  # retry with backoff
except NonRetryableAPIError:
    raise  # fail fast
```

Runnable proof: [`examples/retry_vs_fail_fast.py`](examples/retry_vs_fail_fast.py)

**Mistake 2 — retrying immediately, with no backoff**

```python
# WRONG -- hammering a rate-limited or overloaded service with immediate
# retries makes the underlying problem WORSE, not better.
for attempt in range(5):
    try:
        return call_api()
    except RetryableAPIError:
        continue  # no delay at all between attempts
```

```python
# BETTER -- exponential backoff with jitter spaces retries out and avoids
# many clients retrying in lockstep at the exact same moments.
await asyncio.sleep(backoff_delay(attempt))
```

Runnable proof: [`examples/exponential_backoff_jitter.py`](examples/exponential_backoff_jitter.py)

**Mistake 3 — retrying forever against a service that's fully down**

```python
# WRONG -- with no circuit breaker, every caller keeps retrying (with
# backoff or not) against a service that's clearly not coming back soon,
# wasting time and resources on both sides.
```

```python
# BETTER -- a circuit breaker opens after enough consecutive failures,
# rejecting calls immediately for a cooldown period instead of trying.
```

Runnable proof: [`examples/circuit_breaker.py`](examples/circuit_breaker.py)

## 11. ⚡ Quick Tricks

```python
# Classify by exception TYPE, not by parsing error strings
except RetryableAPIError:
    ...
```

```python
# Exponential backoff with jitter, capped
delay = min(cap, base * 2 ** (attempt - 1)) + random.uniform(0, jitter_max)
```

```python
# Fail fast on the errors that will never succeed on retry
except NonRetryableAPIError:
    raise
```

```python
# Combine with a semaphore (module 12) to bound total retry-storm concurrency
async with semaphore:
    await call_with_retry(...)
```

## 12. Performance Considerations

- Backoff delays trade latency for reliability -- tune `base`/`cap` to your actual latency
  budget; a 5-second cap might be fine for a background job but far too slow for a
  user-facing request.
- A circuit breaker avoids the worst-case cost of retries at scale: without one, N concurrent
  callers all retrying against a dead service multiplies load on (and load *from*) a service
  that needs recovery time, not more traffic.

## 13. 🎤 Interview Questions

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

## 14. 🛠 Mini Exercise

Write `classify_status(status_code: int) -> bool` that returns `True` for retryable HTTP
status codes (429, 500, 502, 503, 504) and `False` for everything else, then write
`call_with_retry_by_status(fn, *, max_attempts=3)` that calls `fn()` (which returns an
integer status code, or raises on genuine network failure), retrying only while
`classify_status` says to.

<details>
<summary>Solution</summary>

```python
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def classify_status(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


def call_with_retry_by_status(fn, *, max_attempts: int = 3) -> int:
    for attempt in range(1, max_attempts + 1):
        status = fn()
        if not classify_status(status):
            return status  # success, or a non-retryable status -- stop either way
        if attempt == max_attempts:
            return status  # exhausted retries, return the last (failing) status
    raise AssertionError("unreachable")


calls = {"n": 0}


def flaky_status() -> int:
    calls["n"] += 1
    return 429 if calls["n"] < 3 else 200


print(call_with_retry_by_status(flaky_status))  # 200
```

</details>

## 15. Real-World Challenge

Extend [`examples/circuit_breaker.py`](examples/circuit_breaker.py)'s `CircuitBreaker` so
`HALF_OPEN` only fully closes after a configurable number of *consecutive* successes (not
just one), reverting straight back to `OPEN` on any failure during the half-open trial period
-- the more realistic behavior real circuit breaker libraries implement.

## 16. Cheat Sheet

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

---

⬅ Back to [main README](../README.md)
