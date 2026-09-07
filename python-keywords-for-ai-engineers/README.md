# Python Keywords for AI Engineers

A categorized quick-reference to every Python keyword — through the lens of AI engineering.
Each entry shows the keyword's syntax, a mental model, a production AI use case, and the
gotcha that trips people up.

> This is **not** a beginner keyword list. It covers all 35 Python keywords with the depth
> and context an AI engineer needs — why each keyword matters when you're building LLM apps,
> RAG systems, agents, and production AI services.

---

## Priority Cheatsheet

| Must Know | Daily Use | Situational |
|---|---|---|
| def, return, class, async, await, if, else, for, try, except, with, import, from, yield | True, False, None, and, or, not, in, is, elif, raise, as, lambda, finally, break, continue | match, case, type, assert, global, nonlocal, del, while, pass |

---

## Categories

| # | Category | Keywords Covered | File |
|---|---|---|---|
| 01 | **Values & Identity** | True, False, None, is, in | [01-values-identity.md](01-values-identity.md) |
| 02 | **Boolean Logic** | and, or, not | [02-boolean-logic.md](02-boolean-logic.md) |
| 03 | **Control Flow** | if, elif, else, match, case | [03-control-flow.md](03-control-flow.md) |
| 04 | **Loops & Iteration** | for, while, break, continue, pass | [04-loops-iteration.md](04-loops-iteration.md) |
| 05 | **Functions & Lambdas** | def, return, lambda, yield | [05-functions-lambdas.md](05-functions-lambdas.md) |
| 06 | **Async & Await** | async, await | [06-async-await.md](06-async-await.md) |
| 07 | **Classes & Scope** | class, type, global, nonlocal, del | [07-classes-scope.md](07-classes-scope.md) |
| 08 | **Error Handling & Resources** | try, except, finally, raise, assert, with, import, from, as | [08-error-handling-resources.md](08-error-handling-resources.md) |

---

## Entry Format

Every keyword entry follows this structure:

```
## `keyword`
**Syntax:** `keyword expression` (canonical usage form)
**When to use:** one line, production AI engineering context
**Mental model:** one memorable analogy

\```python
# Real AI engineering use case — 10-20 lines, copy-paste ready
\```

**Gotcha:** one common mistake or footgun to avoid
```

---

## How to Use This Section

- **Learning:** Read categories 05-06 first (functions + async) — they define how every AI backend is structured.
- **Reference:** Use the priority cheatsheet above to decide what to study next based on your current work.
- **Building:** Each code snippet is designed to be copy-pasted into a real project and adapted.
- **Interview prep:** The mental models give you one-line answers for "explain X" questions.

This section complements the numbered modules (`01-functions/` through `28-ai-engineering-patterns/`) and
[`python-builtins-for-ai-engineers/`](../python-builtins-for-ai-engineers/) — those go deep on concepts
and the stdlib; this covers the language keywords themselves.
