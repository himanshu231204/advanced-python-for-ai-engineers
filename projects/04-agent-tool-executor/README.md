# Project 04 — Agent Tool Executor

**Status:** ✅ Written

An executor that lets an agent select and run tools asynchronously, with retries.

## Architecture

```text
Agent decides on a tool call: (tool_name, args)
 ↓
ToolExecutor.execute(tool_name, args)
 ↓
look up the tool by name -- unknown name -> structured failure, no exception raised
 ↓
run the tool, retrying only TransientToolError with exponential backoff
 ↓
ToolExecutionResult (succeeded / output / error / attempts)
```

## Requirements

- Typed tool interface (`Protocol`-based) so tools are swappable
- Async execution of the selected tool
- Retry logic for transient tool failures
- Structured result/error reporting back to the agent

## Modules used

`11-protocols-generics`, `12-concurrency`, `15-error-handling-retries`, `28-ai-engineering-patterns`

## How it works

`tools.py` defines a `Tool` Protocol (a `name` attribute and an async `run(args)` method) --
any object with that shape can be executed, with no shared base class required. Three
concrete tools demonstrate the executor's behavior:

- `SearchDocsTool` -- always succeeds
- `FlakyApiTool` -- fails with a `TransientToolError` a fixed number of times, then succeeds
  (deterministic, so the retry behavior is reproducible)
- `BrokenTool` -- raises a plain `ValueError`, representing a real bug that retrying can
  never fix

`executor.py`'s `ToolExecutor.execute` retries ONLY `TransientToolError` with exponential
backoff; any other exception is treated as non-retryable and reported back immediately, and
an unknown tool name never raises -- it returns a `ToolExecutionResult(succeeded=False)`
just like any other failure.

## Run it

```bash
pip install -r requirements.txt
python3 executor.py
```

Expected output:

```text
[OK] tool=search_docs attempts=1: found 2 result(s) for 'contextvars'
[OK] tool=flaky_api attempts=3: flaky_api result for 'fetch weather' (succeeded on attempt 3)
[FAILED] tool=broken_tool attempts=1: broken_tool cannot handle args: 'anything'
[FAILED] tool=no_such_tool attempts=0: no such tool: 'no_such_tool'
```

## What this demonstrates

- A `Protocol`-typed tool interface -- the executor depends on a shape, not a concrete base
  class, so new tools can be added without touching the executor
- Retrying only the specific exception type known to be transient, exactly the distinction
  covered in `debugging/exercises/06-retrying-non-retryable-error`
- Every tool call, whatever happens, comes back as the same typed `ToolExecutionResult` --
  the agent never has to catch an exception to know a tool call failed

---

⬅ Back to [projects](../README.md)
