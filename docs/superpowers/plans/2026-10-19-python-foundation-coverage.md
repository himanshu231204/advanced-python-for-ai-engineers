# Python Foundation Coverage Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkboxes for tracking.

**Goal:** Cover the skills in the user's reference image without duplicating existing advanced lessons, placing core data structures in module 00.

**Architecture:** Module 00 provides the prerequisite refresher and links to the deeper numbered modules and supplementary references. Extend existing modules only where the audit identifies a practical workflow gap. Keep each example independently runnable and regenerate the study-site content after lesson changes.

**Tech Stack:** Python 3.12+, standard library for foundation examples; existing pytest, mypy, and uv tooling only in the modules that need them.

**Spec:** User's nine-item reference image, explicit placement of core data structures in module 00, and repository `AGENTS.md` sections 4–9. This document records the coverage audit and the remaining implementation decisions.

## Coverage audit — 2026-10-19

“Covered” means substantive explanations/examples exist in the local repository; it does
not certify every pre-existing example was executed during this audit. “Partial” means
related material exists but the prerequisite explanation or connected workflow is missing.

| Image requirement | Existing evidence | Result / action |
|---|---|---|
| Clean, idiomatic Python: functions, classes, modules, comprehensions, exceptions, stdlib | `01-functions/README.md`, `10-advanced-oop/README.md`, `15-error-handling-retries/README.md`, `23-packaging-modern-python/README.md`, builtins and keywords references | **Partial:** functions/classes/exceptions/stdlib covered; write a structured comprehension and import refresher in 00 |
| Core data structures: lists, tuples, sets, dicts, iterators, generators, when to choose each | `02-iterators-generators/README.md`, `24-performance-memory/README.md`; 00 was a stub | **Gap addressed in this change:** 00 now teaches the four containers and compares iterables/iterators/generators; 02 remains the full iterator/generator lesson |
| Type hints, dataclasses/Pydantic, static analysis | `07-type-hints/README.md`, `08-dataclasses/README.md`, `09-pydantic/README.md`, `11-protocols-generics/README.md` | **Covered:** static checking includes mypy diagnostics/commands; add an optional reproducible local checker exercise, not another typing lesson |
| Mutability, references, scope, exceptions, context managers, failure modes | `24-performance-memory/README.md`, `code-reading/exercises/04-mutability-shared-references.md`, `01-functions/README.md`, `python-keywords-for-ai-engineers/07-classes-scope.md`, `05-context-managers/README.md`, debugging exercises | **Partial:** good deeper coverage; add an explicit LEGB/rebinding refresher to 00 |
| Files, paths, env vars, JSON, CSV, basic serialization | `18-serialization/README.md`, `18-serialization/examples/pathlib_basics.py`, `21-config-environments/README.md`, `python-builtins-for-ai-engineers/03-io-streaming.md`, `python-builtins-for-ai-engineers/04-data-serialization.md` | **Covered:** CSV has reader/writer examples; add navigation links, not a duplicate file-I/O module |
| Sync vs async, concurrent API calls without blocking | `03-asyncio/README.md`, `12-concurrency/README.md`, `13-httpx-async-http/examples/concurrent_api_calls.py` | **Covered:** use these existing lessons; no new async implementation needed |
| Environments and dependencies with uv | `23-packaging-modern-python/README.md`, `23-packaging-modern-python/examples/demo_project/pyproject.toml`, `uv.lock`, project README | **Covered:** uv sync/add/run, isolation, lockfile, src-layout demo already exist; link them from the foundation route |
| Modules and packages rather than a single script | `23-packaging-modern-python/examples/demo_project/src/demo_pkg/`, `python-keywords-for-ai-engineers/08-error-handling-resources.md` | **Partial:** real package plus import reference exist; add an explicit module-vs-package, absolute/relative import, `python -m` walkthrough |
| pytest, debugging with stack traces/logs/breakpoints | `19-testing-pytest/README.md`, `20-logging-observability/README.md`, `python-builtins-for-ai-engineers/05-observability-debug.md`, `python-builtins-for-ai-engineers/14-testing-reliability.md`, `debugging/exercises/` | **Covered across sections:** breakpoints and pdb commands already exist. Add a connected debugging practice route, rather than claiming these are missing |

## Global constraints

- Target Python 3.12+; type-annotate runnable examples.
- Follow all 16 topic-template sections for each finished lesson, with Tiny/Practical/AI examples.
- Keep network access and credentials unnecessary for foundation exercises.
- Complete one topic before starting the next; never mark the whole module Written prematurely.
- Use existing folders and reference docs; no new top-level curriculum folder.
- Preserve the existing advanced lessons; cross-link rather than copy them wholesale.
- Do not add a repo-wide dependency environment for independent lessons.

## Review focus

- Container deduplication preserves retrieval rank and different chunks from one document.
- Hashability and shallow-copy behavior are explained without implying deep tuple immutability.
- Comprehensions do not conceal side effects or introduce accidental eager streaming.
- Import exercises work from the repository root and do not depend on a custom PYTHONPATH.
- Debugger practice is opt-in and never blocks normal example/test execution.

## Task 1 — Core data structures in module 00

**Files:** `00-python-foundation-review/README.md`, `00-python-foundation-review/examples/core_data_structures.py`, `README.md`, `CHEATSHEET.md`, `INTERVIEW.md`, `docs/content.json`.

**Interfaces:** `select_chunks(ranked: list[tuple[str, int]], text_by_chunk: dict[tuple[str, int], str]) -> list[str]`; `unique_document_ids(chunks: list[tuple[str, int]]) -> list[str]`; `count_stock(skus: list[str]) -> dict[str, int]`.

- [x] Write all 16 topic sections for list/tuple/set/dict, with selection tables, hashability, ordering, aliasing, nested copies, and iterator/generator links.
- [x] Add deterministic inventory and ranked-retrieval examples, with runnable assertions for empty input, duplicates, multiple chunks in one document, missing keys, and nested copy behavior.
- [x] Run the script on Python 3.12+; verify the exact documented output and all assertions (verified on Python 3.13.1).
- [x] Execute every Python code fence in the new lesson independently (9 snippets passed; 16 topic sections checked).
- [x] Update navigation/status references and regenerate `docs/content.json`; retain 00's Planned status with an explicit partial-completion description (120 local link targets and bundled lesson/example checked).

## Task 2 — Remaining foundation refreshers

**Create, one topic at a time:**
- `00-python-foundation-review/control-flow-comprehensions.md`
- `00-python-foundation-review/examples/comprehensions.py`
- `00-python-foundation-review/functions-scope.md`
- `00-python-foundation-review/examples/scope_and_references.py`
- `00-python-foundation-review/exception-basics.md`
- `00-python-foundation-review/examples/exception_basics.py`

**Modify:** `00-python-foundation-review/README.md`, `CHEATSHEET.md`, `INTERVIEW.md`, `docs/content.json`.

**Interfaces:** Standalone scripts with `main() -> None`, no imports between examples.

- [ ] Write the full comprehension topic: readable loops vs list/set/dict comprehensions vs generator expressions; filtering, duplicate-key overwrite, comprehension scope, and side-effect avoidance. AI example: filter scored retrieval hits without reordering them.
- [ ] Run its example with empty input, repeated keys, and filtered-out hits; assert that the expected order and duplicate policy are explicit.
- [ ] Write the full scope topic: LEGB, name binding vs mutation, local assignment, `UnboundLocalError`, closures, global/nonlocal tradeoffs, and mutable defaults. Link module 01 instead of reproducing its full function curriculum.
- [ ] Run scope examples checking independent request state and a closure's retained state; include an intentionally failing case caught only for demonstration.
- [ ] Write exception basics: narrow `except`, propagation, `else`, `finally`, `raise ... from ...`, and cleanup links to module 05. AI example: reject malformed local tool arguments with a useful error cause.
- [ ] Run cases for valid input, invalid input, unexpected exception propagation, and cleanup on success/failure.
- [ ] Link these lessons from 00 and ensure each topic is visible on the study site. The builder currently embeds child Markdown as code attachments; use a small builder extension for navigable subtopics if needed, with a check that each child doc appears once in navigation and its parent README link resolves.

## Task 3 — Modules/imports walkthrough and foundation study route

**Create:** `00-python-foundation-review/modules-imports.md`, `23-packaging-modern-python/examples/demo_project/src/demo_pkg/__main__.py`, `23-packaging-modern-python/examples/demo_project/src/demo_pkg/context.py`.

**Modify:** `00-python-foundation-review/README.md`, `ROADMAP.md`, `docs/content.json`.

**Interfaces:** `format_context(parts: list[str]) -> str` in `demo_pkg/context.py`; `demo_pkg/__main__.py` calls it using an explicit relative import. Reuse the existing demo package and its environment; other modules have no import-time side effects.

- [ ] Write all 16 sections: module vs package, `__init__.py`, absolute/relative imports, `__name__`, `python -m`, import caching, circular imports, and avoiding files named after stdlib modules.
- [ ] From the repository root run `uv run --project 23-packaging-modern-python/examples/demo_project python -m demo_pkg`, checking output `First\nSecond`; explicitly explain package execution versus running `__main__.py` as a path.
- [ ] Check importing the package emits no output, and demonstrate the expected relative-import error from direct path execution with the corrected command alongside it.
- [ ] Add a compact “image checklist → lesson” route in ROADMAP linking files/JSON/CSV/env vars, uv, typing/models, async HTTP, pytest, logging, tracebacks, and pdb references from the audit table.

## Task 4 — Optional practice improvements and final status cleanup

**Create:** `07-type-hints/examples/typecheck_contract.py`, `debugging/exercises/07-traceback-to-breakpoint/README.md`, `broken.py`, `fixed.py` in that exercise folder.

**Modify:** `07-type-hints/README.md`, `debugging/README.md`, `00-python-foundation-review/README.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `CHEATSHEET.md`, `INTERVIEW.md`, `docs/content.json`.

**Interfaces:** A typed dispatch contract with one intentional type mismatch for checker practice; a local malformed retrieval record for debugging, with no interactive breakpoint on the normal execution path.

- [ ] Provide an isolated `uvx --from mypy mypy <file>` exercise with the intentional diagnostic and a corrected version. Verify checker failure before correction and success afterward. Keep the intentional failure out of broad “all examples must type-check” claims.
- [ ] Connect the debugging workflow: reproduce, read exception type/message and application frames, inspect local state/logs, use opt-in `python -m pdb <broken.py>`, fix, then add a focused pytest regression assertion. Link existing pdb commands and observability lessons.
- [ ] Verify normal execution terminates without stdin; the corrected example and pytest case pass, while the broken example reproduces its documented exception.
- [ ] Once all foundation topics meet the full template and run, mark 00 Written and update the root progress table and stale AGENTS/CLAUDE status paragraphs. Remove only the completed Planned items.
- [ ] Rebuild the study-site bundle, check local Markdown links/navigation, and run `git diff --check`. Do not claim all old lessons have been revalidated.

## Execution boundary

Task 1 is explicitly requested for this change. Tasks 2–4 are the plan for subsequent
additions; the optional workflow improvements strengthen already-covered subjects and
are not prerequisites for saying those subjects exist in the repository.
