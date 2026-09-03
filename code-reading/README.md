# Code Reading Practice

**Status:** 🚧 Planned (not yet written)

Short Python snippets where the goal is to **predict the outcome before running the code** —
output, execution order, exceptions raised, memory behavior, or async scheduling order.

This trains reading intuition, not typing speed — the same skill you need when reviewing a
teammate's async/agent code or debugging someone else's LLM pipeline.

## Format each exercise will follow

```text
1. Snippet          -> read-only, don't run it yet
2. Your Prediction   -> output / order / exception / memory behavior
3. Answer            -> what actually happens
4. Why               -> the mechanism that explains it
5. Mental Model      -> the general rule to remember
```

## Planned categories

- Iterators & generators (evaluation order, exhaustion)
- Async/await execution order and event-loop scheduling
- Closures and late binding
- Mutability and shared references
- Decorator ordering and `functools.wraps`
- Exception propagation across sync/async boundaries

---

⬅ Back to [main README](../README.md)
