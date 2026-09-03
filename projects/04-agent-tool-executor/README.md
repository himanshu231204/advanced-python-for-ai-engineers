# Project 04 — Agent Tool Executor

**Status:** 🚧 Planned (not yet written)

An executor that lets an agent select and run tools asynchronously, with retries.

## Architecture

```text
Agent
 ↓
Tool selection
 ↓
Async tool execution
 ↓
retry
 ↓
result
```

## Requirements

- Typed tool interface (`Protocol`-based) so tools are swappable
- Async execution of the selected tool
- Retry logic for transient tool failures
- Structured result/error reporting back to the agent

## Modules used

`11-protocols-generics`, `12-concurrency`, `15-error-handling-retries`, `28-ai-engineering-patterns`

---

⬅ Back to [projects](../README.md)
