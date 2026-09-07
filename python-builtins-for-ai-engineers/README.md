# Python Builtins for AI Engineers

A quick-reference guide to Python's standard library through the lens of AI engineering.
Every module entry includes a production use case, a copy-paste code snippet, and a mental
model to make it stick.

> This is **not** a stdlib tour. It covers only the builtins that matter when you're building
> LLM applications, RAG systems, AI agents, and production AI services — and shows you
> exactly how they're used in that context.

---

## Priority Cheatsheet

| Must Know | Daily Use | Situational |
|---|---|---|
| asyncio, abc, dataclasses, typing, logging, re, json, collections, itertools, sqlite3 | functools, contextlib, enum, pathlib, subprocess, inspect, uuid, unittest.mock | mmap, hmac, gzip, heapq, bisect, contextvars, shelve |

---

## Categories

| # | Category | Modules Covered | File |
|---|---|---|---|
| 01 | **Async & Concurrency** | asyncio, concurrent.futures, threading, multiprocessing, queue | [01-async-concurrency.md](01-async-concurrency.md) |
| 02 | **Abstractions & Patterns** | abc, dataclasses, typing, functools, contextlib | [02-abstractions-patterns.md](02-abstractions-patterns.md) |
| 03 | **I/O & Streaming** | io, socket, ssl, struct, selectors | [03-io-streaming.md](03-io-streaming.md) |
| 04 | **Data & Serialization** | json, pickle, csv, codecs, base64 | [04-data-serialization.md](04-data-serialization.md) |
| 05 | **Observability & Debug** | logging, traceback, inspect, warnings, cProfile | [05-observability-debug.md](05-observability-debug.md) |
| 06 | **Time, State & Control** | time/datetime, signal, atexit, enum, weakref | [06-time-state-control.md](06-time-state-control.md) |
| 07 | **OS & System** | os/pathlib, sys, subprocess, shutil, tempfile | [07-os-system.md](07-os-system.md) |
| 08 | **Text, Regex & Math** | re, string, hashlib, math/statistics, random/secrets | [08-text-regex-math.md](08-text-regex-math.md) |
| 09 | **Iteration & Functional** | itertools, collections.Counter, collections.defaultdict, operator | [09-iteration-functional.md](09-iteration-functional.md) |
| 10 | **Config & Environment** | configparser, tomllib, argparse, os.environ pattern | [10-config-environment.md](10-config-environment.md) |
| 11 | **Compression & Binary** | gzip, zlib, tarfile, zipfile, mmap | [11-compression-binary.md](11-compression-binary.md) |
| 12 | **Networking & Protocols** | http.client, urllib.parse, smtplib, uuid | [12-networking-protocols.md](12-networking-protocols.md) |
| 13 | **Security & Crypto** | hmac, secrets, hashlib (extended), uuid pattern | [13-security-crypto.md](13-security-crypto.md) |
| 14 | **Testing & Reliability** | unittest, unittest.mock, doctest, pdb/breakpoint | [14-testing-reliability.md](14-testing-reliability.md) |
| 15 | **Data Structures & Algo** | heapq, bisect, array, copy | [15-data-structures-algo.md](15-data-structures-algo.md) |
| 16 | **Persistence & DB** | sqlite3, shelve, xml.etree, html.parser | [16-persistence-db.md](16-persistence-db.md) |
| 17 | **Concurrency (Advanced)** | contextvars, gc | [17-concurrency-advanced.md](17-concurrency-advanced.md) |

---

## Entry Format

Every module entry follows this structure:

```
## `module_name`
**Import:** `import module` or `from module import X`
**When to use:** one line, production AI engineering context
**Mental model:** one memorable analogy

\```python
# Real AI engineering use case — 10-20 lines, copy-paste ready
\```

**Gotcha:** one common mistake or footgun to avoid
```

---

## How to Use This Section

- **Learning:** Read categories 01-02 first (async + abstractions) — they're the foundation of every AI backend.
- **Reference:** Use the priority cheatsheet above to decide what to learn next based on your current work.
- **Building:** Each code snippet is designed to be copy-pasted into a real project and adapted.
- **Interview prep:** The mental models give you one-line answers for "explain X" questions.

This section complements the numbered modules (`01-functions/` through `28-ai-engineering-patterns/`) — those go deep on a single concept; these go wide across the stdlib.
