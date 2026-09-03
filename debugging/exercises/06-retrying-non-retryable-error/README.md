# Exercise 6 — Retrying a Non-Retryable Error

**Category:** Broken retry logic

## Symptom

```text
failed after 3 attempts
```

The call fails after burning through all 3 retry attempts, even though the error (an invalid
API key) can never succeed no matter how many times it's retried. Run
[`broken.py`](broken.py) and see it for yourself.

## Root Cause

`except Exception as exc:` catches EVERY exception type, including ones that represent a
fundamentally broken configuration (`InvalidApiKeyError`) rather than a transient failure
(`RateLimitedError`). Retrying a non-retryable error wastes time, wastes any per-call cost
(a billed LLM API call), and delays the caller from finding out about a real, fixable
problem.

## Fix

Catch only the specific exception type(s) known to be transient (`RateLimitedError`), and
let a non-retryable error type (`InvalidApiKeyError`) propagate immediately instead. See
[`fixed.py`](fixed.py) -- it fails after exactly 1 attempt instead of 3.

## Takeaway

Retry logic needs to distinguish "this might work if I try again" from "this will never
work no matter how many times I try" -- a bare `except Exception` in a retry loop treats
every failure as the first kind, which is rarely true.
