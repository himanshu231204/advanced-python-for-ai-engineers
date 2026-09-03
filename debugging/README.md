# Debugging Practice

**Status:** 🚧 Planned (not yet written)

Intentionally broken code, one file per bug category. The task is to find and fix the bug
before checking the corrected version — this is deliberate practice for the kind of bugs
that show up constantly in real AI-system code.

## Format each exercise will follow

```text
broken/    -> the intentionally broken implementation + a failing scenario
fixed/     -> the corrected implementation, with a comment explaining the root cause
```

## Planned categories

- Broken async code (missing `await`, blocking calls inside async functions)
- Broken FastAPI endpoints (sync/async mismatches, dependency issues)
- Broken generators (exhausted iterators, incorrect `yield` placement)
- Broken decorators (missing `functools.wraps`, incorrect argument forwarding)
- Broken Pydantic models (validation gaps, mutable defaults)
- Broken concurrency (race conditions, unbounded task creation)
- Broken retry logic (retrying non-retryable errors, missing backoff)
- Broken streaming code (buffering instead of streaming, dropped chunks)

---

⬅ Back to [main README](../README.md)
