# 28 — AI Engineering Patterns

**Level:** 3 (AI-System Python) | **Status:** ✅ Written

This is the capstone module: patterns specific to LLM/RAG/agent systems, built on top of
everything the rest of the curriculum covered -- typed validation (module 09), async
generators (module 04), retries (module 15), and the production patterns from module 27.
Tool-calling interfaces, structured output contracts, streaming pipelines, RAG orchestration,
and evaluation harnesses.

> Examples in this module need `pydantic` and `httpx`. See [`requirements.txt`](requirements.txt).

---

## 1. What is it?

A set of five recurring shapes that show up in almost every real LLM/agent system: turning a
model's tool call into a validated function call, treating a model's JSON output as a
contract instead of free text, streaming partial results through composable stages, combining
retrieval with generation, and measuring pipeline quality with a repeatable test set.

## 2. Why does it exist?

An LLM is a component that returns untyped text (or JSON that *claims* to match a schema) and
that can be slow, wrong, or subtly different between calls. Systems built around one make the
same handful of decisions repeatedly -- how to validate what came back, how to stream partial
output, how to combine retrieval with generation, how to know if a prompt change made things
better or worse. These patterns are the answers the field has converged on.

## 3. 💡 Mental Model

```text
tool call         : LLM emits {name, args} text -> validate args -> call real function
structured output : LLM emits JSON -> validate against a Pydantic contract -> retry if invalid
streaming         : tokens -> small composable async-generator STAGES -> usable partial output
RAG               : query -> retrieve chunks -> augment prompt -> generate -> answer
evaluation        : (input, expected) test cases -> run pipeline -> pass rate, not vibes
```

## 4. Syntax

```python
# Tool calling: validate the model's raw args against a schema before calling anything
validated_args = schema.model_validate(raw_args)
result = fn(validated_args)

# Structured output: treat a validation failure as retryable, not fatal
try:
    return Model.model_validate_json(raw_json)
except ValidationError:
    ...  # retry, don't crash

# Streaming pipeline: chain async generator stages
async def stage_two(upstream: AsyncIterator[str]) -> AsyncIterator[str]:
    async for item in upstream:
        yield transform(item)

# RAG: keep retrieve / augment / generate as separate, swappable functions
chunks = retrieve(query)
prompt = augment_prompt(query, chunks)
answer = await generate(prompt, client)

# Evaluation: run every case, report a rate
results = [EvalResult(case, pipeline(case.input)) for case in cases]
```

## 5. Minimal Example

```python
from pydantic import BaseModel

class SearchArgs(BaseModel):
    query: str

def search(args: SearchArgs) -> str:
    return f"searched for {args.query}"

validated = SearchArgs.model_validate({"query": "contextvars"})
print(search(validated))
```

## 6. What happens internally? (structured output + retry)

```text
call LLM with a JSON-mode/structured-output request
      │
      ▼
Model.model_validate_json(raw_response)
      │
      ├── succeeds -> return the validated object
      │
      └── raises ValidationError
              │
              ▼
        retry with the SAME prompt (or one that includes the error)
              │
              ├── succeeds on retry -> return the validated object
              └── fails again -> surface as a real failure, don't loop forever
```

## 7. Comparison: the five patterns

| Pattern | Problem it solves | Key primitive | Module it builds on |
|---|---|---|---|
| Tool calling | model output isn't a real function call | Pydantic schema + dispatch table | 09-pydantic, 10-advanced-oop |
| Structured output | model output isn't guaranteed valid JSON | `model_validate_json` + retry | 09-pydantic, 15-error-handling-retries |
| Streaming pipeline | one giant function is hard to test/extend | chained async generators | 04-async-generators-streaming |
| RAG orchestration | generation alone can't know private/recent facts | typed retrieve → augment → generate | 13-httpx-async-http |
| Evaluation harness | "looks right" isn't a repeatable signal | (input, expected) cases + pass rate | 19-testing-pytest |

## 8. 🎯 AI Engineering Use Case

Every pattern in this module *is* the AI engineering use case -- there's no separate "toy"
version to contrast against.

### Example A — Tiny

```python
class SearchArgs(BaseModel):
    query: str
```

### Example B — Practical

```python
async def generate(prompt: str, client: httpx.AsyncClient) -> str:
    response = await client.post("https://llm.example/generate", json={"prompt": prompt})
    return response.json()["answer"]
```

### Example C — AI Engineering

```python
async def answer_question(query: str, client: httpx.AsyncClient) -> str:
    chunks = retrieve(query)                       # 1. retrieve
    prompt = augment_prompt(query, chunks)          # 2. augment
    return await generate(prompt, client)           # 3. generate
```

Full runnable versions:
[`examples/tool_calling_interface.py`](examples/tool_calling_interface.py),
[`examples/structured_output_contract.py`](examples/structured_output_contract.py),
[`examples/streaming_pipeline.py`](examples/streaming_pipeline.py),
[`examples/rag_orchestration.py`](examples/rag_orchestration.py),
[`examples/evaluation_harness.py`](examples/evaluation_harness.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
AI ENGINEERING PATTERNS
✅ Good for:
- any system where an LLM's output drives a real function call, a stored record, or a
  user-facing answer
- pipelines that need to be graded on more than one example before shipping a prompt change

❌ Avoid when:
- a single hardcoded prompt-and-print script for personal exploration -- these patterns
  earn their keep once the pipeline has more than one caller or more than one test case
- the "tool" is trivial enough that a plain if/else on the model's text is genuinely clearer

BETTER ALTERNATIVE
Start with the plain version while exploring; add the schema/dispatch table, the retry
loop, or the eval harness once the pipeline is heading toward production or needs to be
compared against a previous version.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — calling a function with the model's raw arguments, unvalidated**

```python
# WRONG -- trusts the model's JSON args to already match what the function expects
def dispatch(name, raw_args):
    return TOOLS[name](**raw_args)  # a wrong type here blows up inside the function
```

```python
# BETTER -- validate against a schema first, fail with one clear error
def dispatch(name, raw_args):
    schema, fn = TOOLS[name]
    return fn(schema.model_validate(raw_args))
```

**Mistake 2 — treating a model's JSON response as already correct**

```python
# WRONG -- json.loads succeeding doesn't mean the SHAPE is right
data = json.loads(raw_response)
total = data["total_cents"]  # KeyError or wrong type surfaces far from the real cause
```

```python
# BETTER -- one Pydantic model call reports every problem at once
invoice = ExtractedInvoice.model_validate_json(raw_response)
```

Runnable proof: [`examples/structured_output_contract.py`](examples/structured_output_contract.py)

**Mistake 3 — "eyeballing" a few outputs instead of running a fixed eval set**

```python
# WRONG -- no record of what was tested, no way to compare against the next prompt change
print(classify_sentiment("I love this"))  # looks right, ship it
```

```python
# BETTER -- a fixed set of cases with a pass rate that can be re-run after any change
results = run_evaluation(classify_sentiment, cases)
print(summarize(results))  # e.g. "3/4 passed (75%)"
```

Runnable proof: [`examples/evaluation_harness.py`](examples/evaluation_harness.py)

## 11. ⚡ Quick Tricks

```python
# Give every tool call a typed, self-documenting schema
class SearchDocsArgs(BaseModel):
    query: str
    top_k: int = 3
```

```python
# Keep RAG's three steps swappable and independently testable
def retrieve(query: str) -> list[Chunk]: ...
def augment_prompt(query: str, chunks: list[Chunk]) -> str: ...
async def generate(prompt: str, client) -> str: ...
```

```python
# One-line eval summary
f"{passed}/{len(results)} passed ({passed / len(results):.0%})"
```

## 12. Performance Considerations

- Validating a tool call's arguments with Pydantic is cheap relative to the network round
  trip to the LLM itself -- never skip it to "save time."
- Streaming stages should do minimal work per item (buffer append, cheap string check) --
  expensive per-token processing defeats the purpose of streaming, which is showing partial
  output quickly.
- An evaluation harness that calls a real LLM per case gets slow and costly fast; run it
  against a cached/mocked pipeline during development and reserve real calls for a smaller,
  periodic run.

## 13. 🎤 Interview Questions

**Q: Why validate a model's tool-call arguments instead of calling the function directly with
them?**
A: The model can emit malformed or wrongly-typed arguments (a string where an int is
expected, a missing required field). Validating against a schema first turns that into one
clear, catchable error at the dispatch boundary instead of an arbitrary exception deep inside
the tool's own code.

**Q: What's the benefit of splitting a streaming pipeline into separate async generator
stages instead of one function that does everything?**
A: Each stage becomes independently testable and replaceable -- the accumulator or the
sentence-splitter can be swapped or unit tested without needing a real token source, and the
same accumulator stage can be reused in a pipeline that ends differently.

**Q: Why keep retrieve, augment, and generate as three separate functions in a RAG
pipeline?**
A: It lets each piece be replaced independently -- swap the retriever for a real vector DB,
or the generator for a different LLM provider, without touching the orchestration logic that
wires them together, and lets each be unit tested with the other two mocked out.

**Q: Why does an evaluation harness need a fixed set of (input, expected) cases instead of
manually checking a few outputs?**
A: Manual spot-checks aren't repeatable or comparable -- there's no way to tell if a prompt
or model change made things better or worse. A fixed case set with a pass rate gives a single
number to compare across changes.

## 14. 🛠 Mini Exercise

Add a `send_slack_message` tool (with a `channel: str` and `text: str` schema) to
[`examples/tool_calling_interface.py`](examples/tool_calling_interface.py)'s `ToolRegistry`,
then dispatch a call to it.

<details>
<summary>Solution</summary>

```python
class SendSlackMessageArgs(BaseModel):
    channel: str
    text: str


def send_slack_message(args: SendSlackMessageArgs) -> str:
    return f"posted to #{args.channel}: {args.text!r}"


registry.register("send_slack_message", SendSlackMessageArgs, send_slack_message)
print(registry.dispatch("send_slack_message", {"channel": "general", "text": "deploy done"}))
# posted to #general: 'deploy done'
```

</details>

## 15. Real-World Challenge

Extend [`examples/evaluation_harness.py`](examples/evaluation_harness.py) to also report
which specific cases failed in a separate `failures` list returned alongside the summary
string, so a CI job could fail the build only when a *regression* (a case that used to pass)
appears, rather than on every non-100% run.

## 16. Cheat Sheet

```text
AI ENGINEERING PATTERNS
↓

TOOL CALLING       model emits {name, args} -> validate args against a schema -> dispatch
STRUCTURED OUTPUT  model emits JSON -> Model.model_validate_json -> retry on ValidationError
STREAMING          chain small async-generator stages, each transforming the last
RAG                retrieve(query) -> augment_prompt(query, chunks) -> generate(prompt)
EVALUATION         fixed (input, expected) cases -> run pipeline -> pass rate, not vibes

WHEN TO USE
-> any LLM-driven system whose output triggers a real function, a record, or a shipped answer

COMMON MISTAKE
-> calling a tool/parsing a response without validating it against a schema first

AI USE CASE
-> this module IS the AI engineering use case -- these are the shapes real LLM/RAG/agent
   systems are built from
```

---

⬅ Back to [main README](../README.md)
