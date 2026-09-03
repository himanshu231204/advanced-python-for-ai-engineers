# Debugging Practice

**Status:** ✅ Written

Intentionally broken code, one file per bug category. The task is to find and fix the bug
before checking the corrected version — this is deliberate practice for the kind of bugs
that show up constantly in real AI-system code.

## How to use these

For each exercise: run `broken.py`, read the symptom, and try to diagnose and fix the root
cause yourself before opening `fixed.py` and the exercise's `README.md`. Every file has
actually been run and its documented output verified.

## Format each exercise follows

```text
broken.py   -> the intentionally broken implementation + a demonstration of the symptom
fixed.py    -> the corrected implementation
README.md   -> Symptom -> Root Cause -> Fix -> Takeaway
```

## Exercises

| # | Exercise | Category |
|---|---|---|
| 1 | [Missing `await`](exercises/01-missing-await/) | Broken async code |
| 2 | [Blocking Call Inside an Async Function](exercises/02-blocking-call-in-async/) | Broken async code |
| 3 | [Exhausted Generator Reused](exercises/03-exhausted-generator/) | Broken generators |
| 4 | [Decorator Silently Drops the Return Value](exercises/04-decorator-drops-return-value/) | Broken decorators |
| 5 | [Pydantic Model With No Real Validation](exercises/05-pydantic-mutable-default/) | Broken Pydantic models |
| 6 | [Retrying a Non-Retryable Error](exercises/06-retrying-non-retryable-error/) | Broken retry logic |

---

⬅ Back to [main README](../README.md)
