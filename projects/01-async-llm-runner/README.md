# Project 01 — Async LLM Runner

**Status:** ✅ Written

A concurrent runner that fires multiple LLM calls at once, safely.

## Requirements

- Async API calls to an LLM (mocked here so the project runs offline and deterministically)
- Bounded concurrency (semaphore-limited fan-out)
- Retries with exponential backoff on transient failures
- Per-call timeout handling
- Structured (Pydantic) result objects
- Structured logging of successes/failures/timing

## Modules used

`03-asyncio`, `12-concurrency`, `15-error-handling-retries`, `20-logging-observability`, `09-pydantic`

## How it works

```text
run_all(prompts)
      │
      ▼
asyncio.gather over run_one(index, prompt, semaphore) for each prompt
      │
      ▼   (semaphore bounds how many of these run AT ONCE)
run_one: for attempt in 1..max_attempts:
      │
      ├── asyncio.wait_for(call_llm(...), timeout)  -- per-call timeout
      │       │
      │       ├── success            -> return LLMCallResult(succeeded=True)
      │       ├── PermanentLLMError  -> return LLMCallResult(succeeded=False) immediately
      │       └── TransientLLMError  -> sleep(backoff), try again
      │
      └── ran out of attempts -> return LLMCallResult(succeeded=False)
```

`mock_llm.py` stands in for a real provider client -- each prompt index has a fixed,
deterministic failure pattern (some succeed immediately, one recovers after one retry, one
never recovers, one is a permanent/non-retryable failure), so the run's output is
reproducible without a real network call.

## Run it

```bash
pip install -r requirements.txt
python3 runner.py
```

Expected output (attempt-order across concurrent prompts may vary slightly, but the final
summary is deterministic):

```text
3/5 prompts succeeded
[OK] index=0 attempts=1: response to 'summarize the contextvars module' (succeeded on attempt 1)
[OK] index=1 attempts=2: response to 'explain exponential backoff' (succeeded on attempt 2)
[OK] index=2 attempts=1: response to 'what is a health check' (succeeded on attempt 1)
[FAILED] index=3 attempts=3: prompt 3 attempt 3: rate limited
[FAILED] index=4 attempts=1: prompt 4 rejected by content policy
```

## What this demonstrates

- A `Semaphore` bounding concurrent LLM calls instead of firing all of them at once
- `asyncio.wait_for` enforcing a per-call timeout independent of retry logic
- Retrying only the specific exception type that represents a transient failure
  (`TransientLLMError`), while a `PermanentLLMError` returns immediately -- see
  `28-ai-engineering-patterns` and `debugging/exercises/06-retrying-non-retryable-error`
  for why that distinction matters
- Every call, success or failure, returns a typed `LLMCallResult` rather than raising -- the
  caller gets a complete picture of the batch instead of losing everything to the first
  exception

---

⬅ Back to [projects](../README.md)
