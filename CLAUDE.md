# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## Start here

**[`AGENTS.md`](AGENTS.md) is the source of truth** for this repo's philosophy, folder
structure, and the mandatory topic template/style rules. Read it before writing or editing
any lesson content, cheat sheet, or project — do not improvise a different content format.
This file only adds Claude Code–specific operating notes on top of it.

## Repository shape

- This is a **documentation + example-code learning repository**, not an application. There
  is no single build/run/deploy target — each module and project is self-contained.
- Numbered folders (`00-...` through `28-...`) are learning modules in progression order.
  `code-reading/`, `debugging/`, and `projects/` are practice/application folders.
- Every module folder currently holds a stub `README.md` (scope only). Writing a module means
  replacing that stub with a full topic file per `AGENTS.md` §4 — not appending to it.

## Working conventions in this repo

- Keep one topic's content self-contained in its module folder. If a runnable example needs
  a dependency (e.g. `httpx`, `pydantic`, `fastapi`), add a small `requirements.txt` or a
  `# /// script` PEP 723 header inside that module/project folder rather than a single
  repo-wide dependency file — modules should stay independently runnable.
- Don't fill in multiple modules in one pass "for efficiency" — finish one module to the full
  template before starting the next, so the repo is never left with half-written topics.
- When adding runnable code, actually run it (or a representative snippet) before committing
  — every example in this repo is expected to execute as shown.
- Favor `python3.12+` syntax; call out clearly if an example needs a specific version.

## Commands

No package manager or test suite exists at the repo root yet (per-module/project
`requirements.txt` or `pyproject.toml` files will be added as those are built). Until then:

```bash
python3 --version        # confirm 3.12+
python3 path/to/example.py
```

If a project folder gains its own `pyproject.toml`/`uv` setup, prefer `uv run` inside that
folder and document the exact command in that project's `README.md`.

## Scope discipline

This repo intentionally does not teach basic Python from scratch, unrelated web-dev topics,
or a specific LLM provider's SDK in depth — see `AGENTS.md` §10 before adding content that
might drift outside scope.
