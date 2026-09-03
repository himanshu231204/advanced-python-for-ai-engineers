# AGENTS.md — How to Work in This Repository

This file is the operating manual for any AI agent (or human) adding content to
`advanced-python-for-ai-engineers`. It defines the repository's philosophy, structure, and
the exact template every topic must follow. Read this before writing or editing any lesson
content, cheat sheet, or project.

For Claude Code specifically, see [`CLAUDE.md`](CLAUDE.md) — it points back here for content
rules and adds session/tooling-specific notes.

---

## 1. What this repository is

A practical, interview-ready, production-oriented **Advanced/Modern Python learning system
for AI Engineers** — not a generic Python course, and not a book. It teaches Python concepts
that matter for building LLM applications, RAG systems, AI agents, LangGraph-style workflows,
FastAPI AI backends, async LLM APIs, streaming applications, tool-calling systems, and
production AI services.

Every topic must be written from this angle:

> Why does an AI Engineer need this Python concept, how does it work internally, how do I use
> it in an AI system, and when should I NOT use it?

Never write a topic as generic, textbook-style Python content with no AI-engineering framing.

## 2. Current status

This repository is being built incrementally. The full directory structure exists; module
folders currently contain a `README.md` **stub** (scope + planned subtopics) rather than
finished lessons. A module is "done" only once its `README.md` follows the full
[topic template](#4-the-topic-template) with runnable code — not before. Don't assume a
module is finished just because the folder exists; check its status line.

## 3. Repository structure

```text
advanced-python-for-ai-engineers/
│
├── README.md                 Main entry point, learning order, setup
├── AGENTS.md                 This file — content rules for any agent
├── CLAUDE.md                 Claude Code–specific operating notes
├── ROADMAP.md                phased learning roadmap
├── CHEATSHEET.md             master cheat sheet index
├── INTERVIEW.md              (planned) interview question bank
├── PATTERNS.md               (planned) reusable pattern library
├── GLOSSARY.md                (planned) term glossary
├── PYTHON_TO_AI_ENGINEERING.md (planned) concept -> application map
│
├── 00-python-foundation-review/   Foundation
├── 01-functions/                  Level 1
├── 02-iterators-generators/       Level 1
├── 03-asyncio/                    Level 1
├── 04-async-generators-streaming/ Level 1
├── 05-context-managers/           Level 1
├── 06-decorators/                 Level 1
├── 07-type-hints/                 Level 2
├── 08-dataclasses/                Level 2
├── 09-pydantic/                   Level 2
├── 10-advanced-oop/               Level 4
├── 11-protocols-generics/         Level 2
├── 12-concurrency/                Level 3
├── 13-httpx-async-http/           Level 3
├── 14-streaming-sse-websockets/   Level 3
├── 15-error-handling-retries/     Level 3
├── 16-caching/                    Level 3
├── 17-queues-background-tasks/    Level 3
├── 18-serialization/              Level 2
├── 19-testing-pytest/             Level 2
├── 20-logging-observability/      Level 3
├── 21-config-environments/        Level 2
├── 22-dependency-injection/       Level 2
├── 23-packaging-modern-python/    Level 2
├── 24-performance-memory/         Level 4
├── 25-gil-processes-threads/      Level 4
├── 26-contextvars/                Level 4
├── 27-production-python-patterns/ Level 3
├── 28-ai-engineering-patterns/    Level 3
│
├── code-reading/              Predict-the-output exercises
├── debugging/                 Intentionally broken code + fixes
└── projects/                  6 mini projects combining modules
```

New topics get added inside the closest existing numbered module. Only create a new
top-level folder if a topic genuinely doesn't fit any existing one — keep the progression
intact rather than fragmenting it.

## 4. The topic template

Every finished topic file (a module's `README.md`, or a dedicated `.md` inside it) MUST use
this structure. Skipping sections is not allowed for a topic marked "done"; a short "not
applicable" is acceptable only when a section genuinely doesn't apply (e.g. no async
variant exists).

```text
1.  What is it?
2.  Why does it exist?
3.  Mental Model
4.  Syntax
5.  Minimal Example
6.  Step-by-Step Execution (or: Internal Working)
7.  Comparison (vs the nearest related concept — table format)
8.  AI Engineering Use Case
9.  When to Use / When NOT to Use (decision box, see §6)
10. Common Mistakes (🚨 wrong code -> better code -> why)
11. Quick Tricks (⚡ copy-pasteable one-liners/snippets)
12. Performance Considerations (where relevant)
13. Interview Questions (🎤 with answers)
14. Mini Exercise (🛠)
15. Real-World / Runnable Code Example
16. Cheat Sheet (scannable summary)
```

Every code example set must include, where the concept supports it:

- **Example A — Tiny**: smallest possible snippet.
- **Example B — Practical**: a realistic, non-AI application.
- **Example C — AI Engineering**: the same concept inside an LLM/RAG/agent/API/streaming
  context.

## 5. The "When to Use" decision box

Every non-trivial concept needs this exact shape:

```text
WHEN TO USE
✅ Good for:
- ...

WHEN NOT TO USE
❌ Avoid when:
- ...

BETTER ALTERNATIVE
Use X instead when Y.
```

## 6. Style rules

- Concise, practical, engineering-focused. No academic filler, no repeated explanations.
- Target ratio per topic: **20% explanation / 50% code / 20% diagrams & tables / 10%
  interview & practice.**
- Beginner-friendly wording is fine; simplistic or hand-wavy explanations are not.
- Occasional short Hinglish intuition asides are fine (e.g. "*Yaad rakho: generator ek
  baar consume ho gaya toh dobara nahi chalega.*"), but the core technical explanation
  must stay in clear English.
- Use these labels consistently:
  `💡 Mental Model` `⚡ Quick Trick` `🚨 Common Mistake` `🎯 AI Use Case`
  `🔥 High ROI` `🧠 Deep Dive` `🎤 Interview` `🛠 Practice`
- Mark concept importance where useful: `MUST KNOW`, `HIGH ROI`, `GOOD TO KNOW`,
  `OPTIONAL / DEEP DIVE`. Don't over-index on obscure CPython internals.
- Use ASCII diagrams for anything with a sequence or flow (event loop, generator state,
  task scheduling, producer/consumer, retry flow, request lifecycle, streaming, agent
  architecture). Keep diagrams simple — arrows and boxes, not art.
- Use comparison tables liberally (Purpose / Mental Model / Syntax / Performance / AI Use
  Case / When to use / When not to use as columns).

## 7. Code quality requirements

- Target Python 3.12+ syntax where it's idiomatic (e.g. modern generics, `match`).
- All code must be runnable and small — one concept per snippet, no kitchen-sink examples.
- Type-annotate everything.
- Comment only the non-obvious "why" (a subtle invariant, a workaround, a gotcha) — never
  restate what a well-named line already says.
- No unused imports, no dead code, no speculative abstractions "for later."
- Prefer real async patterns (`httpx.AsyncClient`, `asyncio.gather`) over toy sleeps when
  demonstrating AI-engineering examples — mock the network call, don't fake the pattern.

## 8. Common-mistakes catalogue to draw from

Forgetting `await` · blocking calls inside async functions · `time.sleep()` in async code ·
unbounded concurrent task creation · mutable default arguments · decorators without
`functools.wraps` · incorrect type assumptions · Pydantic misuse (e.g. mutable defaults,
over-validating) · swallowing exceptions · retrying non-retryable errors · unbounded queues ·
accidental shared state across async tasks or threads.

## 9. Adding a new module or project

1. Read this file and the target folder's existing `README.md` stub (scope + subtopics).
2. Write the module following the [topic template](#4-the-topic-template).
3. Update that module's status line from `🚧 Planned` to `✅ Written`.
4. Cross-link relevant cheat sheets / `PATTERNS.md` entries once they exist.
5. Update the root `README.md` progress table if one exists at that point.
6. Never invent a new top-level doc (`ROADMAP.md`, `PATTERNS.md`, etc.) without checking
   whether it's already listed in this file's structure section — keep names consistent.

## 10. What this repo intentionally does not teach

Basic Python syntax from scratch, general web development unrelated to AI backends, a
specific LLM provider's SDK in depth, or LangGraph/LangChain internals themselves (module 28
and Project 06 teach the *Python patterns* those frameworks rely on, not the frameworks).
