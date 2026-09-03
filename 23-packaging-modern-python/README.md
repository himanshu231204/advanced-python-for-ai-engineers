# 23 — Packaging & Modern Python Tooling

**Level:** 2 (Production Python) | **Status:** ✅ Written

Modern Python projects are built and shipped differently than they were five years ago --
`pyproject.toml`, `uv`, and `Ruff` are the current standard toolchain. This module is less
about writing Python code and more about the project structure and tooling every module in
this repo (and any real project) relies on.

> This module's examples include an actual runnable project
> ([`examples/demo_project/`](examples/demo_project/)) plus a Ruff before/after pair. Try the
> commands below yourself if you have `uv`/`ruff` installed -- every command and its output
> shown in this file was actually run against these exact files.

---

## 1. What is it?

`pyproject.toml` is the single, standardized configuration file for a Python project's
metadata, dependencies, and tool settings (replacing the old `setup.py`/`setup.cfg`/
`requirements.txt` patchwork). `uv` is a fast, modern package/project manager built to work
with it. `Ruff` is an extremely fast linter and formatter, usually replacing several older
tools (flake8, isort, Black) at once.

## 2. Why does it exist?

Before `pyproject.toml`, a project's build config, dependencies, and tool settings were
scattered across `setup.py`, `setup.cfg`, `requirements.txt`, and separate config files for
each linter/formatter. Consolidating all of it into one standardized, declarative file (and
building fast, modern tools around it) makes projects easier to set up, understand, and keep
consistent.

## 3. 💡 Mental Model

```text
pyproject.toml   -> the ONE file describing what your project is and needs
uv               -> creates the environment, installs dependencies, runs commands in it
ruff check        -> finds problems (unused imports, style issues, likely bugs)
ruff format       -> rewrites code to a consistent style automatically
```

## 4. Syntax

```toml
# pyproject.toml
[project]
name = "demo-pkg"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.6"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py312"
```

```bash
uv sync              # create .venv, install everything pyproject.toml declares
uv add httpx          # add a new dependency (updates pyproject.toml + uv.lock)
uv run pytest         # run a command inside the project's environment
ruff check .          # lint
ruff format .         # format
```

## 5. Minimal Example

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []
```

```bash
uv sync
uv run python -c "print('hello from the managed environment')"
```

## 6. What happens internally?

```text
uv sync
        │
        ▼
uv reads pyproject.toml (and uv.lock, if present, for exact pinned versions)
        │
        ▼
creates (or reuses) a .venv for this project, isolated from the system
Python and from any other project's environment
        │
        ▼
installs every dependency listed, writing/updating uv.lock with exact
resolved versions -- so `uv sync` on another machine reproduces the SAME
environment, not just "compatible" versions
```

## 7. Comparison: The Old Way vs `pyproject.toml` + `uv` + `Ruff`

| | Old way | Modern way |
|---|---|---|
| Project metadata/deps | `setup.py`, `requirements.txt` | one `pyproject.toml` |
| Environment management | manual `venv` + `pip install` | `uv sync` (fast, reproducible via `uv.lock`) |
| Linting | flake8 | `ruff check` |
| Import sorting | isort | `ruff check` (built-in `I` rules) |
| Formatting | Black | `ruff format` |
| Speed | several separate, slower tools | one fast tool (Ruff), one fast manager (`uv`) |

## 8. 🎯 AI Engineering Use Case

Every module in this repository that needs a dependency (`pydantic`, `httpx`, `fastapi`)
follows exactly this shape at a larger scale: a `pyproject.toml` declaring what's needed, a
`src/` package layout, and `uv run`/`ruff` as the actual commands a contributor runs.

### Example A — Tiny

```toml
[project]
name = "my-tool"
requires-python = ">=3.12"
dependencies = []
```

### Example B — Practical

```
demo_project/
├── pyproject.toml
├── src/
│   └── demo_pkg/
│       ├── __init__.py
│       └── core.py
└── tests/
    └── test_core.py
```

### Example C — AI Engineering

A production AI service's `pyproject.toml` declares `fastapi`, `httpx`, and `pydantic` as
dependencies, `pytest`/`ruff` as a dev-only dependency group, and `uv run uvicorn app:app`
(or similar) as the actual command that starts the service -- the same pattern as
[`examples/demo_project/`](examples/demo_project/), just with real dependencies.

## 9. WHEN TO USE / WHEN NOT TO

```text
pyproject.toml + uv + Ruff
✅ Use for:
- any project with dependencies, even a small one -- reproducibility from
  day one is cheap and pays off immediately
- keeping linting/formatting consistent across contributors automatically

❌ Don't:
- hand-maintain a requirements.txt alongside pyproject.toml -- pick one
  system (pyproject.toml + a lockfile) and avoid the two drifting apart
- skip a lockfile (uv.lock) for anything beyond a true one-off script --
  "works on my machine" is exactly what lockfiles prevent

BETTER ALTERNATIVE
For a genuinely tiny, dependency-free script, a single .py file (or a
PEP 723 inline script header) is simpler than a full project layout --
reserve pyproject.toml for anything with real dependencies or that will
be shared/reused.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — unused imports left in committed code**

```python
# WRONG -- clutters the file and hints at half-finished refactors
import os
import sys
from collections import OrderedDict

def messy(a, b):
    return a + b
```

```python
# BETTER -- ruff check --fix removes these automatically
def messy(a: int, b: int) -> int:
    return a + b
```

Real captured output from `ruff check` against
[`examples/ruff_before.py`](examples/ruff_before.py):

```text
F401 [*] `os` imported but unused
F401 [*] `sys` imported but unused
F401 [*] `collections.OrderedDict` imported but unused
F841 Local variable `x` is assigned to but never used
Found 4 errors.
[*] 3 fixable with the `--fix` option (1 hidden fix can be enabled with the `--unsafe-fixes` option).
```

**Mistake 2 — inconsistent formatting left for reviewers to nitpick**

```python
# WRONG -- inconsistent spacing that a formatter should have caught
def messy(  a,b ):
    x=1
    return a+b
```

```python
# BETTER -- ruff format fixes this automatically, with no manual effort
def messy(a, b):
    x = 1
    return a + b
```

Real captured `ruff format --diff` output against the same file:

```diff
-def messy(  a,b ):
-    x=1
-    return a+b
+def messy(a, b):
+    x = 1
+    return a + b
```

**Mistake 3 — no lockfile, so "it works on my machine" happens constantly**

```text
# WRONG -- requirements.txt with loose version ranges (or none at all)
# means two developers (or dev vs. production) can end up on different
# resolved versions of the same declared dependencies.
```

```bash
# BETTER -- commit uv.lock alongside pyproject.toml so `uv sync` installs
# the EXACT same resolved versions everywhere, every time.
```

## 11. ⚡ Quick Tricks

```bash
uv add <package>            # add + install a new dependency
uv add --dev <package>       # add a dev-only dependency (tests, linting)
uv run <command>             # run anything inside the project's environment
ruff check --fix .           # auto-fix everything Ruff safely can
ruff format .                # reformat the whole project
```

```toml
# Keep dev-only tools out of the shipped package's dependencies
[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.6"]
```

## 12. Performance Considerations

- `uv` and `Ruff` are both written in Rust and are dramatically faster than the tools they
  replace (pip, flake8, Black, isort) -- this matters most in CI, where linting/installing
  runs on every single push.
- A committed lockfile (`uv.lock`) trades a small amount of repo size for guaranteed
  reproducibility -- almost always worth it outside of trivial scripts.

## 13. 🎤 Interview Questions

**Q: What problem does `pyproject.toml` solve that the old `setup.py`/`requirements.txt`
combination didn't?**
A: It consolidates project metadata, dependencies, build configuration, and tool settings
into one standardized, declarative file instead of scattering them across multiple files with
inconsistent formats -- making projects easier to understand, more consistent across tools,
and less error-prone to maintain.

**Q: What does a lockfile (`uv.lock`) actually guarantee that `pyproject.toml` alone doesn't?**
A: `pyproject.toml` typically declares dependency *ranges* (e.g. `httpx>=0.27`); a lockfile
pins the exact resolved versions of every dependency (and transitive dependency) that were
installed. `uv sync` using the lockfile reproduces the identical environment every time,
rather than potentially resolving to different (but technically compatible) versions on
different machines or at different times.

**Q: What does Ruff replace, and why is that consolidation useful?**
A: Ruff combines the functionality of several older tools -- flake8 (linting), isort (import
sorting), and largely Black (formatting) -- into one fast tool with one configuration section
in `pyproject.toml`, instead of maintaining separate configs and separate slow tool
invocations for each.

**Q: Why put a package's source code under `src/` instead of directly at the project root?**
A: The `src/` layout prevents accidentally importing the package via a stray current-
directory `sys.path` entry instead of the actually-installed version -- forcing tests (and
any other code) to only see the package if it's genuinely installed (even in editable mode),
which catches packaging mistakes that a flat layout can hide.

## 14. 🛠 Mini Exercise

Given this snippet, list every issue Ruff's default rule set (`E`, `F`, import sorting `I`)
would flag, then write the corrected version:

```python
import sys
import json

def add(a,b):
    unused = 5
    return a+b
```

<details>
<summary>Solution</summary>

Issues: `json`/`sys` both unused (`F401`), `unused` assigned but never used (`F841`),
missing spaces around operators/after commas, unsorted imports (moot here since both are
unused and would be removed).

```python
def add(a: int, b: int) -> int:
    return a + b
```

</details>

## 15. Real-World Challenge

Add a `[tool.ruff.lint.per-file-ignores]` section to
[`examples/demo_project/pyproject.toml`](examples/demo_project/pyproject.toml) that allows
unused imports (`F401`) specifically in `__init__.py` files (a common, legitimate pattern for
re-exporting a package's public API), and confirm with `ruff check` that it no longer flags
`src/demo_pkg/__init__.py` while still flagging unused imports elsewhere.

## 16. Cheat Sheet

```text
PACKAGING & MODERN TOOLING
↓

pyproject.toml               single source of truth: metadata, deps, tool config
uv sync                       create .venv, install exactly what's declared
uv add <pkg> / --dev <pkg>    add a runtime / dev-only dependency
uv run <command>              run inside the project's managed environment
uv.lock                        exact, reproducible dependency versions

ruff check .                  lint (unused imports, likely bugs, style)
ruff check --fix .            auto-fix what's safely fixable
ruff format .                  consistent formatting, no manual effort

src/<package>/                the modern package layout

WHEN TO USE
-> any project with real dependencies -- reproducibility from day one

COMMON MISTAKE
-> no lockfile committed -> "works on my machine" across different resolved versions

AI USE CASE
-> the exact toolchain behind every module's requirements.txt in this repo, at project scale
```

---

⬅ Back to [main README](../README.md)
