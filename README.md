# Advanced Python for AI Engineers

A practical, interview-ready, production-oriented **Advanced/Modern Python learning system —
built specifically for AI Engineers.**

This is not a generic Python course. Every topic exists to answer one question:

> **Why does an AI Engineer need this Python concept, how does it work internally, how do I
> use it in an AI system, and when should I NOT use it?**

> 🚧 **Status: under active construction.** The full folder structure and curriculum outline
> are in place; module content is being written incrementally. Each module's `README.md`
> shows its own status (`🚧 Planned` or `✅ Written`) — see [Progress](#progress) below.

---

## Who this is for

Engineers who already know basic Python and are building (or want to build) LLM apps, RAG
systems, AI agents, LangGraph-style workflows, FastAPI AI backends, or production AI
services — and want their Python to hold up under real concurrency, real failure modes, and
real interviews.

## What this teaches

- Modern Python core: iterators, generators, async/await, context managers, decorators
- Production Python: type hints, dataclasses, Pydantic, testing, packaging, config
- AI-system Python: asyncio concurrency, async HTTP, streaming (SSE/WebSockets), retries,
  caching, background tasks
- Deep Python: memory model, the GIL, threads vs. processes, contextvars, magic methods
- Reusable patterns for LLM/RAG/agent architectures, and the interview questions that go
  with all of the above

## What this intentionally does NOT teach

- Basic Python syntax from scratch (variables, loops, `if`/`else`)
- General web development unrelated to AI backends
- A specific LLM provider's SDK in depth
- LangGraph/LangChain internals themselves — Module 28 and Project 06 teach the *Python
  patterns* those frameworks are built on, not the frameworks

## Skill map

```text
Python
 ↓
Modern Python        (iterators, generators, decorators, context managers)
 ↓
Async Python         (asyncio, async generators, streaming)
 ↓
Production Python     (typing, Pydantic, testing, packaging, config)
 ↓
AI Engineering Python (concurrency, HTTPX, retries, caching, background jobs)
 ↓
LLM / RAG / Agents
 ↓
Production AI Systems
```

## Learning order

The repo is organized into four levels, roughly in build order:

| Level | Focus | Modules |
|---|---|---|
| Foundation | Quick review before diving in | `00` |
| **Level 1** — Modern Python Core | iterators, generators, async/await, context managers, decorators | `01`–`06` |
| **Level 2** — Production Python | type hints, dataclasses, Pydantic, protocols, serialization, testing, config, DI, packaging | `07`–`09`, `11`, `18`, `19`, `21`–`23` |
| **Level 3** — AI-System Python | concurrency, HTTPX, streaming, retries, caching, queues, logging, production/AI patterns | `12`–`17`, `20`, `27`, `28` |
| **Level 4** — Deep Python | advanced OOP/magic methods, performance & memory, GIL/processes/threads, contextvars | `10`, `24`–`26` |

Work top to bottom through the numbered folders (`00-...` → `28-...`); each module lists
prerequisites in its own `README.md`. `code-reading/` and `debugging/` can be done alongside
any level. `projects/` are meant to be attempted after their listed prerequisite modules.

## Repository structure

```text
advanced-python-for-ai-engineers/
├── README.md, AGENTS.md, CLAUDE.md   ← you are here / agent & content rules
├── 00-python-foundation-review/  … 28-ai-engineering-patterns/   ← the curriculum
├── code-reading/                  predict-the-output exercises
├── debugging/                     intentionally broken code + fixes
└── projects/                      6 mini projects combining modules
```

See [`AGENTS.md`](AGENTS.md) for the full structure, the mandatory topic template, and the
content style rules every module follows once written.

## Progress

| Status | Meaning |
|---|---|
| 🚧 Planned | Folder + scope exist; full lesson not yet written |
| ✅ Written | Follows the full topic template with runnable code |

| Module | Status |
|---|---|
| [`01-functions`](01-functions/) | ✅ Written |
| [`02-iterators-generators`](02-iterators-generators/) | ✅ Written |
| [`03-asyncio`](03-asyncio/) | ✅ Written |
| [`04-async-generators-streaming`](04-async-generators-streaming/) | ✅ Written |
| [`05-context-managers`](05-context-managers/) | ✅ Written |
| [`06-decorators`](06-decorators/) | ✅ Written |
| [`07-type-hints`](07-type-hints/) | ✅ Written |
| [`08-dataclasses`](08-dataclasses/) | ✅ Written |
| [`09-pydantic`](09-pydantic/) | ✅ Written |
| [`10-advanced-oop`](10-advanced-oop/) | ✅ Written |
| [`11-protocols-generics`](11-protocols-generics/) | ✅ Written |
| [`12-concurrency`](12-concurrency/) | ✅ Written |
| [`13-httpx-async-http`](13-httpx-async-http/) | ✅ Written |
| [`14-streaming-sse-websockets`](14-streaming-sse-websockets/) | ✅ Written |
| [`15-error-handling-retries`](15-error-handling-retries/) | ✅ Written |
| [`16-caching`](16-caching/) | ✅ Written |
| [`17-queues-background-tasks`](17-queues-background-tasks/) | ✅ Written |
| [`18-serialization`](18-serialization/) | ✅ Written |
| [`19-testing-pytest`](19-testing-pytest/) | ✅ Written |
| [`20-logging-observability`](20-logging-observability/) | ✅ Written |
| [`21-config-environments`](21-config-environments/) | ✅ Written |
| [`22-dependency-injection`](22-dependency-injection/) | ✅ Written |
| [`23-packaging-modern-python`](23-packaging-modern-python/) | ✅ Written |
| [`24-performance-memory`](24-performance-memory/) | ✅ Written |
| [`25-gil-processes-threads`](25-gil-processes-threads/) | ✅ Written |
| [`26-contextvars`](26-contextvars/) | ✅ Written |
| [`27-production-python-patterns`](27-production-python-patterns/) | ✅ Written |
| [`28-ai-engineering-patterns`](28-ai-engineering-patterns/) | ✅ Written |
| everything else | 🚧 Planned |

Check each folder's `README.md` for its current status and planned subtopics.

## Setup

- **Python version:** 3.12+
- No repo-wide dependencies yet — each module/project is self-contained and will list its
  own requirements as it's written (a small `requirements.txt` or PEP 723 script header
  inside that folder).

```bash
git clone https://github.com/himanshu231204/advanced-python-for-ai-engineers.git
cd advanced-python-for-ai-engineers
python3 --version   # confirm 3.12+
```

## How to run examples

Once a module contains runnable code, run it directly:

```bash
python3 01-functions/example.py
```

If a project folder has its own `pyproject.toml` (added as projects are built), use `uv run`
from inside that folder instead — see that project's `README.md`.

## How to run tests

Testing conventions live in [`19-testing-pytest/`](19-testing-pytest/). Most module examples
are self-checking (they print expected output) rather than backed by a test suite; project
05 has a real `pytest` suite — see [`projects/05-production-ai-service`](projects/05-production-ai-service/).

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for a phased, paced path through the curriculum (with
checkpoints and an alternative order for readers who already know foundational Python), and
[`AGENTS.md`](AGENTS.md) for how content gets added.

## Reference docs

Cross-curriculum references that sit alongside the numbered modules:

- [`ROADMAP.md`](ROADMAP.md) — phased learning path with checkpoints
- [`CHEATSHEET.md`](CHEATSHEET.md) — every module's cheat sheet in one scannable page
- [`INTERVIEW.md`](INTERVIEW.md) — every module's interview questions in one bank

## Contributing / extending

This repo is built module-by-module. If you're adding content (human or AI agent), read
[`AGENTS.md`](AGENTS.md) first — it defines the exact template, style, and structure every
topic must follow so the repo stays consistent as it grows.
