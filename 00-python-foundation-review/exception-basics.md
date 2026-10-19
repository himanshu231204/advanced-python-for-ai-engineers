# Exception Basics — MUST KNOW

**Status:** ✅ Written | Python 3.12+ | Standard library only

## 1. What is it?

An exception is an object describing a failed operation. Raising it interrupts the normal
path until Python finds a matching handler. AI services need explicit boundaries between
bad caller inputs and unexpected implementation or infrastructure failures.

| Part | Meaning | Example |
|---|---|---|
| Type | Category used to select a handler | `ValueError` |
| Message | Human-readable detail, `str(exc)` | `invalid literal for int()...` |
| Traceback | Stack locations leading to the failure | Caller -> parser -> failing line |

A traceback helps locate a bug; a message alone does not identify the execution path.
Avoid exposing raw tracebacks or sensitive tool arguments to end users.

## 2. Why does it exist?

A function cannot return a valid result when parsing fails. Exceptions carry that failure
through callers without making every function return a special sentinel. Catch an error
where you can recover, translate it into a useful domain error, or report it responsibly.

## 3. 💡 Mental Model

```text
caller -> tool dispatcher -> argument parser
                               |
                               +-- invalid JSON raises JSONDecodeError
                               |
                               v
                       narrow handler adds context
                               |
                       ToolArgumentError (cause retained)
                               |
                               v
                     caller handles invalid arguments

unexpected bug -> no matching handler -> propagates to caller
```

The handler matches an exception class or its subclasses. `except Exception` catches many
unrelated failures; bare `except:` also catches signals such as `KeyboardInterrupt` and
`SystemExit`. Neither belongs around routine argument parsing.

## 4. Syntax

```python
try:
    value: int = int("4")
except ValueError as exc:
    raise ValueError("count must contain digits") from exc
else:
    assert value == 4
finally:
    cleanup_ran: bool = True
assert cleanup_ran
```

`else` runs only when the `try` suite finishes normally. Exceptions raised inside `else`
are not caught by the preceding handlers. `finally` runs on normal completion, exception,
and return during ordinary Python execution; process termination can prevent cleanup.

## 5. Minimal Example

**Example A — Tiny**

```python
try:
    int("many")
except ValueError as exc:
    assert type(exc).__name__ == "ValueError"
    assert "many" in str(exc)
else:
    raise AssertionError("conversion should fail")
```

This deliberate failure is caught so the example exits successfully.

## 6. Step-by-Step Execution

**Example B — Practical: parse a page count**

```python
def page_count(raw: str) -> int:
    try:
        count: int = int(raw)
    except ValueError as exc:
        raise ValueError("page count must be an integer") from exc
    else:
        if count < 1:
            raise ValueError("page count must be positive")
        return count

assert page_count("3") == 3
try:
    page_count("many")
except ValueError as exc:
    assert isinstance(exc.__cause__, ValueError)
else:
    raise AssertionError("invalid page count accepted")
```

```text
"3"    -> int succeeds -> else validates -> return 3
"many" -> int raises   -> except wraps -> caller catches
"0"    -> int succeeds -> else raises  -> caller must handle
```

A bare `raise` inside a handler re-raises the active exception. Use it when observing a
failure without replacing its meaning. `raise NewError(...) from exc` translates the
failure while retaining the explicit cause and its traceback.

## 7. Comparison

| Construct | Purpose | AI use case | Limitation |
|---|---|---|---|
| `if` validation | Reject a known invalid state | Check a tool argument's range | Does not handle failed operations |
| Narrow `except` | Recover from a specific failure | Handle JSON syntax errors | Other exception types propagate |
| `else` | Work after successful `try` | Use a successfully parsed result | Its failures need an outer handler |
| `finally` | Release resources on either path | Close a local context buffer | Cleanup can itself fail |
| `raise ... from ...` | Translate with explicit cause | Add tool-specific context | Adds an exception to the chain |
| `with` | Encapsulate resource lifecycle | Open/close context files | Requires a context manager |

See [context managers, module 05](../05-context-managers/README.md) for reusable cleanup,
and [error handling and retries, module 15](../15-error-handling-retries/README.md) for
production error policies. A validation failure is not a reason to retry automatically.

## 8. 🎯 AI Engineering Use Case

**Example C — AI Engineering: validate local search tool arguments**

Model-generated JSON is external input. JSON syntax validity does not establish the
required object shape, field types, or ranges. Type annotations do not validate runtime
input. This boundary rejects malformed arguments before invoking a tool.

```python
import json

class ToolArgumentError(ValueError):
    """Invalid caller arguments for a local tool."""


def decode_arguments(raw: str) -> tuple[str, int]:
    try:
        arguments: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolArgumentError("search arguments must be valid JSON") from exc
    if not isinstance(arguments, dict):
        raise ToolArgumentError("search arguments must be an object")
    query: object = arguments.get("query")
    limit: object = arguments.get("limit")
    if not isinstance(query, str) or not query.strip():
        raise ToolArgumentError("query must be a non-empty string")
    # bool is an int subclass; exact type rejects JSON true/false.
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ToolArgumentError("limit must be an integer between 1 and 10")
    return query.strip(), limit

assert decode_arguments('{"query": "python", "limit": 2}') == ("python", 2)
try:
    decode_arguments("{")
except ToolArgumentError as exc:
    assert isinstance(exc.__cause__, json.JSONDecodeError)
else:
    raise AssertionError("malformed JSON accepted")
```

The narrow parsing handler leaves unrelated failures visible. A tool implementation's
`RuntimeError` must propagate rather than becoming a misleading invalid-arguments error.
Here extra object fields are ignored; a stricter tool contract could reject them explicitly.

## 9. When to Use / When NOT to Use

```text
WHEN TO USE
✅ Good for:
- Recovering from a specific expected operation failure.
- Translating parser errors at a tool boundary with an explicit cause.
- Releasing a resource during normal completion or failure.

WHEN NOT TO USE
❌ Avoid when:
- A simple condition describes routine branching.
- You cannot recover but would silently discard the failure.
- You want to retry every error, including malformed input.

BETTER ALTERNATIVE
Use if validation for known constraints; use with for supported resource lifecycles.
```

## 10. 🚨 Common Mistakes

**Wrong: swallow failures and produce a plausible success value.**

```python
def wrong_count(raw: str) -> int:
    try:
        return int(raw)
    except Exception:
        return 0

assert wrong_count("broken") == 0  # Demonstrates the concealed failure.
```

**Better: catch the expected conversion failure and preserve its cause.**

```python
def count(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError("count must be an integer") from exc

try:
    count("broken")
except ValueError as exc:
    assert isinstance(exc.__cause__, ValueError)
else:
    raise AssertionError("conversion failure was hidden")
```

The caller can now distinguish failure from a real zero. Keep `try` suites small so a
handler does not accidentally intercept errors from unrelated work.

**Wrong: return from `finally` suppresses a pending exception or return.**

```python
def wrong_result() -> str:
    try:
        raise RuntimeError("index failed")
    finally:
        return "success"

assert wrong_result() == "success"  # Deliberately demonstrates the failure mode.
```

**Better: perform cleanup only; preserve the original outcome.**

```python
from io import StringIO

buffer: StringIO = StringIO("context")
try:
    try:
        raise RuntimeError("index failed")
    finally:
        buffer.close()
except RuntimeError as exc:
    assert str(exc) == "index failed"
else:
    raise AssertionError("failure was suppressed")
assert buffer.closed
```

Cleanup that raises a new exception replaces the propagating exception as the visible
failure (the original normally remains in `__context__`). Prefer proven resource APIs;
do not casually catch and discard cleanup failures either.

## 11. ⚡ Quick Tricks

```python
def require_positive(value: int) -> None:
    if value <= 0:
        raise ValueError("value must be positive")

require_positive(2)
try:
    require_positive(0)
except ValueError as exc:
    details: tuple[str, str] = (type(exc).__name__, str(exc))
    assert details == ("ValueError", "value must be positive")
else:
    raise AssertionError("invalid value accepted")
```

Catch a tuple such as `except (TypeError, ValueError)` only if both require the same
response. Put subclass handlers before broader parent-class handlers.

## 12. Performance Considerations

- Raising and formatting tracebacks costs more than an ordinary branch; avoid exceptions
  as routine per-token control flow.
- Use exceptions for actual failed operations; readability usually matters more than
  micro-optimizing occasional failures.
- Retaining exception objects can retain traceback frames and referenced objects. Avoid
  storing unbounded exception histories in a long-running agent.
- Do not log the same failure at every stack layer; choose the reporting boundary.

## 13. 🎤 Interview Questions

**Does `finally` run after `return`?** During ordinary execution, yes. A return or exception
inside `finally` can replace the pending outcome, so cleanup should avoid control transfers.

**What does `raise ... from exc` add?** An explicit cause in `__cause__`; displayed
tracebacks show both failures and their causal relationship.

**Why catch `JSONDecodeError` instead of `Exception`?** It isolates invalid JSON syntax;
unexpected programming failures remain visible to an outer boundary.

**Are `else` errors caught by the same `except`?** No. That handler covers the `try` suite.

## 14. 🛠 Mini Exercise

Extend `decode_arguments` to reject unknown keys. Check valid input, a missing query,
boolean limit, malformed JSON, and an extra key. Preserve the JSON decoding cause, and
explain why a failure inside the search implementation should propagate unchanged.

## 15. Real-World / Runnable Code Example

Run from the repository root:

```bash
python 00-python-foundation-review/examples/exception_basics.py
```

The [standalone script](examples/exception_basics.py) validates a local tool boundary and
asserts valid input, malformed JSON with a chained cause, wrong shapes/types/ranges,
unexpected tool failure propagation, and buffer cleanup on both success and failure.

```text
Exception basics checks passed.
```

## 16. Cheat Sheet

| Need | Syntax / rule |
|---|---|
| Handle a known failure | `except SpecificError as exc:` |
| Inspect type/message | `type(exc).__name__`, `str(exc)` |
| Preserve current failure | Bare `raise` inside its handler |
| Translate with cause | `raise ToolArgumentError("context") from exc` |
| Success-only work | `else:` after handlers |
| Cleanup on either path | `finally:`; avoid `return` here |
| Resource lifecycle | Prefer `with`; [module 05](../05-context-managers/README.md) |
| Retries / production policy | [Module 15](../15-error-handling-retries/README.md) |

Back to [foundation review](README.md).
