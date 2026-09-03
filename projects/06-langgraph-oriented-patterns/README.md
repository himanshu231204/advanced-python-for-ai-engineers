# Project 06 — LangGraph-Oriented Python Patterns

**Status:** ✅ Written

This project does **not** teach LangGraph itself — it demonstrates the underlying Python
patterns that graph-based agent frameworks (like LangGraph) are built on, so the framework
feels obvious once you use it.

## Requirements

- Typed state objects passed between nodes
- Async node functions
- Generator-based streaming of intermediate state
- A typed tool-calling interface
- Structured (Pydantic) outputs at each node boundary
- Basic retry and observability hooks around node execution

## Modules used

`07-type-hints`, `08-dataclasses`, `09-pydantic`, `04-async-generators-streaming`,
`11-protocols-generics`, `28-ai-engineering-patterns`

## Architecture

```text
run_graph(query, nodes)
      │
      ▼
state = AgentState(query=query)
      │
      ▼
for (node_name, node) in nodes:
      │
      ▼
    run_node_with_retry(node, state)   -- observability + retry around ONE node
      │       │
      │       ├── success -> log elapsed time, return new state
      │       └── error   -> log, retry up to max_attempts, then re-raise
      ▼
    yield state   -- the CALLER sees intermediate state after every node,
                      not just the final result
```

`state.py` defines `AgentState`, a plain Pydantic model passed between every node -- no
node knows about any other node's internals, only the shared state shape. `nodes.py` has
three async nodes (`plan_node`, `tool_node`, `respond_node`), each taking an `AgentState`
and returning a new one via `state.model_copy(update=...)`; `tool_node` dispatches through a
typed `TOOL_REGISTRY: dict[str, Tool]`, the same tool-calling shape from
`28-ai-engineering-patterns`. `graph.py`'s `run_graph` is an async generator that yields the
state after every node completes.

## Run it

```bash
pip install -r requirements.txt
python3 graph.py
```

Expected output:

```text
node=plan attempt=1 status=ok elapsed=0.000s
--- after node, plan='search for: what is contextvars used for?' answer=None
node=tool attempt=1 status=ok elapsed=0.005s
--- after node, plan='search for: what is contextvars used for?' answer=None
node=respond attempt=1 status=ok elapsed=0.000s
--- after node, plan='search for: what is contextvars used for?' answer="Based on 3 result(s) for 'what is contextvars used for?', here's my answer to 'what is contextvars used for?'."

final answer: Based on 3 result(s) for 'what is contextvars used for?', here's my answer to 'what is contextvars used for?'.
```

(Exact elapsed timings will vary slightly run to run.)

## What this demonstrates

- Nodes as plain async functions over one shared, typed state object -- no framework
  required to see why graph-based agent frameworks structure things this way
- Streaming intermediate state via an async generator, so a caller (e.g. a UI) can show
  progress after each step rather than waiting for the whole graph to finish
- A retry-and-observability wrapper applied uniformly around every node, independent of
  what each node actually does
- `state.model_copy(update=...)` producing a new, validated state object per node instead of
  mutating shared state in place

---

⬅ Back to [projects](../README.md)
