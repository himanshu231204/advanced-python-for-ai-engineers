# Modules and Imports — MUST KNOW

**Status:** ✅ Written | **Requires:** Python 3.12+

## 1. What is it?

A **module** is an importable unit, usually one `.py` file. A **package** groups
modules under a shared name. AI services use packages to separate prompt formatting,
retrieval, HTTP clients, and application startup.

This lesson uses the existing [demo project](../23-packaging-modern-python/examples/demo_project/).
Run its commands from the repository root; no model keys or network requests are needed.

## 2. Why does it exist?

Imports let the API, a batch worker, and tests call the same context formatter.
Keeping startup separate from reusable functions prevents importing a helper from
starting a server, printing messages, or contacting a model provider.

## 3. 💡 Mental Model

```text
demo_project/
  pyproject.toml              distribution: demo-pkg
  src/
    demo_pkg/                import package: demo_pkg
      __init__.py            regular package initialization / public exports
      core.py                existing module
      context.py             pure context formatting
      __main__.py            package execution entry point
```

`__init__.py` identifies a regular package and runs when it is first imported.
It may be empty; exports are optional. Namespace packages can omit this file,
but this demo uses a regular package. Distribution names and import names need
not match: `demo-pkg` is installed, while `demo_pkg` is imported.

```text
import demo_pkg.context
       |
       v
sys.modules lookup --> cached? --> return existing module
       |
       +-- absent --> find package/module --> create and cache module
                                               |
                                               v
                                    execute top-level statements
```

Caching is per interpreter process. It does not make module-level mutable state
safe for concurrent requests.

## 4. Syntax

```python
import json
from demo_pkg.context import format_context  # Absolute package path.

payload: str = json.dumps({"context": format_context(["First", "Second"])})
assert json.loads(payload)["context"] == "First\nSecond"
```

Inside `demo_pkg/__main__.py`, the equivalent sibling import is:

```python
from .context import format_context
```

One dot means the current package; two dots mean its parent. Relative imports
need package context. They are not paths relative to the terminal's directory.

## 5. Minimal Example

**Example A — Tiny:** standard-library module plus a named import.

```python
import math
from math import ceil

score: float = math.sqrt(9)
assert score == 3.0
assert ceil(2.1) == 3
```

Python executes a module's top-level code on its first normal import, including
function definitions. A function body runs only when called.

## 6. Step-by-Step Execution

From the repository root:

```bash
uv run --project 23-packaging-modern-python/examples/demo_project python -m demo_pkg
```

```text
uv selects the demo project's environment
  -> Python locates installed demo_pkg
  -> executes demo_pkg/__init__.py
  -> executes demo_pkg/__main__.py with package context
  -> relative import loads demo_pkg.context
  -> __name__ == "__main__": call main()
  -> print formatted context
```

Output:

```text
First
Second
```

On a normal `import demo_pkg.__main__`, that module's `__name__` is
`"demo_pkg.__main__"`, so the guard prevents `main()` from running.
The package initializer still has its ordinary package name during `-m` execution.

## 7. Comparison

| Form | Meaning | Appropriate use | Gotcha |
|---|---|---|---|
| `import demo_pkg.context` | Bind package, access module through it | Explicit module ownership | Call `demo_pkg.context.format_context(...)` |
| `from demo_pkg.context import format_context` | Bind selected name | Call helper directly | Rebinding this name does not update the source module |
| `from .context import format_context` | Import sibling within package | Internal package relationships | Requires package execution/import context |
| `python -m demo_pkg` | Locate package and execute `__main__.py` | CLI backed by reusable package | Package must be discoverable |
| `python path/to/file.py` | Execute file as script | Standalone script without relative imports | Does not establish its containing package |

## 8. 🎯 AI Engineering Use Case

**Example B — Practical:** use the formatter for a printable meeting agenda.

```python
from demo_pkg.context import format_context

agenda: list[str] = ["Review incidents", "Assign follow-ups"]
print(format_context(agenda))
assert agenda == ["Review incidents", "Assign follow-ups"]
```

**Example C — AI Engineering:** preserve retrieval order when building a context
field. Formatting does not validate trust, remove prompt injection, or enforce
a model's token budget; those remain separate boundaries.

```python
from demo_pkg.context import format_context

ranked_chunks: list[str] = ["First", "Second"]
request: dict[str, str] = {
    "question": "What did retrieval return?",
    "context": format_context(ranked_chunks),
}
assert request["context"] == "First\nSecond"
assert ranked_chunks == ["First", "Second"]
```

## 9. When to Use / When NOT to Use

WHEN TO USE

✅ Good for:
- Modules for focused helpers shared by tests, API handlers, and workers.
- Packages for a coherent application or library with several modules.
- `python -m` for package entry points that use internal relative imports.

WHEN NOT TO USE

❌ Avoid when:
- Importing a helper also opens clients, starts servers, or downloads model weights.
- Splitting every tiny function into a separate module makes navigation harder.
- Adding `sys.path` edits merely conceals an uninstalled package.

BETTER ALTERNATIVE

Use explicit startup functions or dependency injection for resource creation;
use a project environment and installed package when imports need discovery.
See [packaging](../23-packaging-modern-python/README.md) for editable installs and `src/` layout.

## 10. 🚨 Common Mistakes

**Wrong: executing a package file directly.** This command intentionally fails:

```bash
uv run --project 23-packaging-modern-python/examples/demo_project python 23-packaging-modern-python/examples/demo_project/src/demo_pkg/__main__.py
```

Expected final error:

```text
ImportError: attempted relative import with no known parent package
```

**Better:** keep package context with the corrected command:

```bash
uv run --project 23-packaging-modern-python/examples/demo_project python -m demo_pkg
```

**Wrong: circular imports that require a name before it is defined.** Save these
two illustrative files together in a disposable directory; `python -c "import a"`
fails because `a` is only partially initialized:

```python
# a.py
from b import label

name: str = "retriever"
```

```python
# b.py
from a import name

label: str = name.upper()
```

**Better:** move shared values/functions into a third module that imports neither
caller, then have both callers import it. A local import may defer a dependency,
but it does not repair a confused dependency direction.

```text
wrong:   a --> b --> a
better:  a --> shared <-- b
```

**Wrong: naming a local file `json.py`, `typing.py`, or `logging.py`.** Python's
search path can select it before the intended standard-library module.
**Better:** rename it to `json_helpers.py` or `app_logging.py`, restart the
interpreter, and inspect the loaded module's origin:

```python
import json

print(json.__file__)
```

**Wrong: printing or making network calls at module scope. Better:** expose a
function and invoke it under a `__name__` guard, as the runnable entry point does.

## 11. ⚡ Quick Tricks

Check package discovery and silent imports from the repository root:

```bash
uv run --project 23-packaging-modern-python/examples/demo_project python -c "import demo_pkg; print(demo_pkg.__file__)"
uv run --project 23-packaging-modern-python/examples/demo_project python -c "import demo_pkg; import demo_pkg.context; import demo_pkg.__main__"
```

The second command prints nothing. Inspect repeated import identity:

```python
import importlib
from types import ModuleType

first: ModuleType = importlib.import_module("demo_pkg.context")
second: ModuleType = importlib.import_module("demo_pkg.context")
assert first is second
```

## 12. Performance Considerations

- First import includes finding/loading code and executing top-level statements.
- Later ordinary imports normally reuse `sys.modules`; a new process starts fresh.
- Bytecode caches can reduce compilation work; they do not skip module execution
  in a fresh interpreter.
- Avoid loading large ML libraries or weights just to import a lightweight helper.
- Local imports can defer expensive optional dependencies, but measure startup and
  first-call latency before adding them. `importlib.reload()` is not a normal
  application startup strategy and can leave existing references stale.
- `format_context` creates one string proportional to total text length; it does
  not copy or mutate the input list. Very large contexts still need a size budget.

## 13. 🎤 Interview Questions

**Module versus package?** A module is an importable unit; a package can contain
submodules. Regular packages have `__init__.py`; namespace packages need not.

**Does importing twice execute code twice?** Usually no: normal imports reuse
the module cached under its name in `sys.modules` within that process.

**Why does the relative import fail with a file path?** Direct file execution
does not establish the package context needed to resolve the leading dot.

**What does the main guard protect?** Code inside it runs when that module is
the program entry point, not during its normal import. Other top-level code
still runs during the first import.

## 14. 🛠 Mini Exercise

Add `render_agenda(items: list[str]) -> str` in a new `demo_pkg/agenda.py`.
Use an explicit relative import of `format_context`, and return numbered agenda
lines. Importing `demo_pkg.agenda` must print nothing.

```text
[]                     -> ""
["Review", "Assign"]   -> "1. Review\n2. Assign"
```

Explain why `python -m demo_pkg` can resolve a relative import while direct
execution of `src/demo_pkg/__main__.py` cannot.

## 15. Real-World / Runnable Code Example

The actual [formatter](../23-packaging-modern-python/examples/demo_project/src/demo_pkg/context.py):

```python
def format_context(parts: list[str]) -> str:
    return "\n".join(parts)
```

The actual [entry point](../23-packaging-modern-python/examples/demo_project/src/demo_pkg/__main__.py):

```python
from .context import format_context


def main() -> None:
    print(format_context(["First", "Second"]))


if __name__ == "__main__":
    main()
```

Set up and check the demo with [uv](../23-packaging-modern-python/README.md):

```bash
uv sync --project 23-packaging-modern-python/examples/demo_project
uv run --project 23-packaging-modern-python/examples/demo_project python -m demo_pkg
uv run --project 23-packaging-modern-python/examples/demo_project pytest 23-packaging-modern-python/examples/demo_project/tests
```

The tests check empty input, preserved order/duplicates/blank parts, unchanged
input, silent imports in a fresh interpreter, and exact CLI output. `print`
adds the final newline; `format_context` itself adds only separators.

## 16. Cheat Sheet

| Need | Use | Remember |
|---|---|---|
| Import public helper | `from demo_pkg.context import format_context` | Package must be discoverable |
| Import sibling internally | `from .context import format_context` | Dot means current package |
| Initialize regular package | `__init__.py` | Keep it lightweight and predictable |
| Execute package | `python -m demo_pkg` | Runs `__main__.py` with package context |
| Protect startup | `if __name__ == "__main__":` | Does not protect other top-level statements |
| Explain repeat imports | `sys.modules` | Process-local cache, not a fresh instance |
| Fix circular dependency | Shared lower-level module | Do not rely on import order |
| Diagnose shadowing | Inspect `module.__file__` | Avoid standard-library filenames |

Back to [foundation review](README.md) · Next: [modern packaging](../23-packaging-modern-python/README.md)
