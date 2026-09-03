# Code Reading Practice

**Status:** ✅ Written

Short Python snippets where the goal is to **predict the outcome before running the code** —
output, execution order, exceptions raised, memory behavior, or async scheduling order.

This trains reading intuition, not typing speed — the same skill you need when reviewing a
teammate's async/agent code or debugging someone else's LLM pipeline.

## How to use these

For each exercise: open the file, read only the "Snippet" section, write down your own
prediction, THEN read the "Answer" / "Why" / "Mental Model" sections. Every snippet has been
run and its documented output verified — don't just trust your gut, check it against the
actual behavior.

## Format each exercise follows

```text
1. Snippet          -> read-only, don't run it yet
2. Your Prediction   -> output / order / exception / memory behavior
3. Answer            -> what actually happens
4. Why               -> the mechanism that explains it
5. Mental Model      -> the general rule to remember
```

## Exercises

| # | Exercise | Category |
|---|---|---|
| 1 | [Generator Exhaustion & Evaluation Order](exercises/01-iterators-generators.md) | Iterators & generators |
| 2 | [Async/Await Execution Order](exercises/02-async-execution-order.md) | Async scheduling |
| 3 | [Closures and Late Binding](exercises/03-closures-late-binding.md) | Closures |
| 4 | [Mutability and Shared References](exercises/04-mutability-shared-references.md) | Mutability |
| 5 | [Decorator Ordering and `functools.wraps`](exercises/05-decorator-ordering.md) | Decorators |
| 6 | [Exception Propagation Across Async Boundaries](exercises/06-exception-propagation-async.md) | Exceptions + async |

---

⬅ Back to [main README](../README.md)
