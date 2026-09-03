# 09 — Pydantic

**Level:** 2 (Production Python) | **Status:** ✅ Written

Pydantic is how raw LLM output becomes trustworthy structured data before it touches business
logic -- validation at the boundary between the model and your system. Where module 08's
dataclasses assume the data is already correct, Pydantic exists precisely because you cannot
assume that about anything coming from an LLM, an API request, or a config file.

> Examples in this module need the `pydantic` package. See
> [`requirements.txt`](requirements.txt) -- `pip install -r requirements.txt` (or
> `pip install pydantic`) before running them.

---

## 1. What is it?

`pydantic.BaseModel` is a class you subclass to declare a data shape using type hints, exactly
like a dataclass -- except Pydantic actually validates every field at construction time,
raising a clear `ValidationError` the moment something doesn't match.

## 2. Why does it exist?

```text
LLM structured output
        ↓
Pydantic validation
        ↓
business logic
        ↓
API response
```

An LLM asked for JSON can still return the wrong type, a missing field, or a hallucinated
enum value. Without a validation boundary, that bad data flows straight into business logic
and fails somewhere confusing, far from its actual cause. Pydantic puts the check exactly
where the untrusted data enters your system.

## 3. 💡 Mental Model

```text
class Model(BaseModel):
    field: SomeType

Model(field=value)
        │
        ▼
Pydantic checks `value` against `SomeType` RIGHT NOW, coercing when it
safely can (e.g. int -> float) and raising ValidationError when it can't
-- unlike a dataclass, which just stores whatever it's given.
```

## 4. Syntax

```python
from pydantic import BaseModel, Field, field_validator, ValidationError

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value.strip()

# Nested models
class Citation(BaseModel):
    source: str
    page: int

class Answer(BaseModel):
    text: str
    citations: list[Citation]

# Parsing untrusted data (e.g. LLM JSON output)
data = {"text": "...", "citations": [{"source": "x", "page": 1}]}
answer = Answer.model_validate(data)   # or Answer(**data)

answer.model_dump()       # -> plain dict
answer.model_dump_json()  # -> JSON string
```

## 5. Minimal Example

```python
from pydantic import BaseModel

class Point(BaseModel):
    x: float
    y: float

p = Point(x=1, y=2)   # int -> float coercion
print(p)              # x=1.0 y=2.0
```

## 6. What happens internally?

```text
Point(x="not a number", y=2)
        │
        ▼
Pydantic's generated validator (compiled once, when the class is defined)
runs against every field
        │
        ▼
"not a number" cannot be coerced to float -> collects an error for field `x`
        │
        ▼
after checking ALL fields (not just the first failure), raises ONE
ValidationError containing every problem found
```

## 7. Comparison: Dataclass vs Pydantic

| | Dataclass (module 08) | Pydantic `BaseModel` |
|---|---|---|
| Validates at runtime? | no | yes, on every construction |
| Type coercion | none | yes, where safe (e.g. `"5"` -> `5` for an `int` field) |
| Error reporting | n/a | a single `ValidationError` listing every failing field |
| Cost | near-zero | real, but small -- worth it at trust boundaries |
| Best for | internal, trusted state | untrusted external data: LLM output, API bodies, config files |

## 8. 🎯 AI Engineering Use Case

Parsing an LLM's JSON response straight into a Pydantic model is the standard pattern for
"structured output": if the model hallucinates a field or an invalid enum value, you find out
immediately, with a specific error -- not three functions downstream.

### Example A — Tiny

```python
class Point(BaseModel):
    x: float
    y: float
```

### Example B — Practical

```python
class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
```

### Example C — AI Engineering

```python
class ExtractedInvoice(BaseModel):
    vendor: str
    amount_usd: float
    status: Literal["paid", "unpaid", "overdue"]

def parse_llm_json(raw_json: str) -> ExtractedInvoice:
    data = json.loads(raw_json)
    return ExtractedInvoice.model_validate(data)
```

Full runnable version: [`examples/structured_llm_output.py`](examples/structured_llm_output.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
PYDANTIC
✅ Good for:
- validating LLM structured output before it reaches business logic
- API request/response bodies (this is what FastAPI uses under the hood)
- config loaded from files/environment variables that could be malformed

❌ Avoid when:
- the data is entirely internal and already trusted (agent run state you
  constructed yourself) -- a dataclass is lighter and just as correct there
- validating the same tiny, hot-path internal object thousands of times per
  second where the validation cost actually matters

BETTER ALTERNATIVE
Use a dataclass (module 08) for internal state you fully control. Reach
for Pydantic specifically at the boundary where untrusted data enters.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — using a dataclass where the data isn't actually trusted**

```python
# WRONG -- a dataclass never checks anything; obviously bad LLM output
# sails straight through and corrupts whatever uses it next.
@dataclass
class ExtractedInvoice:
    vendor: str
    amount_usd: float
    status: str

ExtractedInvoice(vendor="Acme", amount_usd="not a number", status="pending review")
# constructs fine -- no error, no warning, just silently wrong data
```

```python
# BETTER
class ExtractedInvoice(BaseModel):
    vendor: str
    amount_usd: float
    status: Literal["paid", "unpaid", "overdue"]

ExtractedInvoice(vendor="Acme", amount_usd="not a number", status="pending review")
# raises ValidationError immediately, naming exactly what's wrong
```

Runnable proof, side by side: [`examples/dataclass_vs_pydantic.py`](examples/dataclass_vs_pydantic.py)

**Mistake 2 — catching the wrong exception type**

```python
# WRONG -- Pydantic validation failures are ValidationError, not ValueError
# (even though field_validator functions raise ValueError internally --
# Pydantic wraps it).
try:
    SearchRequest(query="", top_k=5)
except ValueError:
    ...  # this technically works since ValidationError subclasses ValueError,
         # but it's imprecise and can accidentally swallow unrelated bugs
```

```python
# BETTER -- catch the specific exception Pydantic actually raises
from pydantic import ValidationError

try:
    SearchRequest(query="", top_k=5)
except ValidationError as e:
    for error in e.errors():
        print(error["loc"], error["msg"])
```

**Mistake 3 — over-validating fields that don't need it**

```python
# WRONG -- excessive custom validators on every field of a hot-path model
# add real overhead for no benefit if the data is already known-good
# (e.g. it just came out of another Pydantic model in the same process).
```

```python
# BETTER -- validate once, at the actual trust boundary; pass already-
# validated model instances around internally without re-validating them.
```

## 11. ⚡ Quick Tricks

```python
# Parse a dict (e.g. from json.loads) straight into a model
MyModel.model_validate(data)
```

```python
# Convert a model back to plain data
instance.model_dump()        # dict
instance.model_dump_json()   # JSON string
```

```python
# See every validation failure at once, not just the first
try:
    MyModel(**bad_data)
except ValidationError as e:
    for err in e.errors():
        print(err["loc"], err["msg"])
```

```python
# Field constraints without a custom validator function
Field(default=5, ge=1, le=20)      # numeric bounds
Field(min_length=1, max_length=500)  # string length
```

## 12. Performance Considerations

- Pydantic v2's validation core is written in Rust and compiled once per model class -- it's
  fast, but it's still real work happening on every construction, unlike a dataclass.
- Validate at the boundary, once. Don't re-validate an object you already constructed and
  trust internally -- pass the model instance around instead of re-parsing dicts repeatedly.

## 13. 🎤 Interview Questions

**Q: Why use Pydantic instead of plain dictionaries for LLM structured output?**
A: A plain dict gives you no guarantee about its shape -- a missing key or wrong type only
surfaces later, wherever the code first tries to use it incorrectly, with a confusing error
far from the actual cause. Pydantic validates the entire shape immediately when the data
arrives, raising one clear error naming every problem, right at the boundary where the
untrusted data entered.

**Q: What's the practical difference between a dataclass and a Pydantic model?**
A: A dataclass generates `__init__`/`__repr__`/`__eq__` from annotations but performs zero
runtime validation -- it will happily store a `str` in a field annotated `int`. A Pydantic
model uses the same annotations to actually validate (and where safe, coerce) every field at
construction time, raising `ValidationError` on a mismatch.

**Q: What exception does Pydantic raise on invalid data, and what does it contain?**
A: `pydantic.ValidationError`. Calling `.errors()` on it returns a list of every failing
field (not just the first), each with a `loc` (the field path, useful for nested models) and
a `msg` describing exactly what went wrong.

**Q: When would a dataclass be the better choice over Pydantic, even in an AI system?**
A: For internal state you construct yourself and fully control -- agent run state, an
intermediate pipeline result -- where there's no untrusted boundary being crossed. Paying
Pydantic's validation cost there buys you nothing, since the data was never at risk of being
malformed in the first place.

## 14. 🛠 Mini Exercise

Define a Pydantic model `ToolCall` with `name: str` (non-empty) and `arguments: dict[str,
object]`, and a function `parse_tool_call(raw: str) -> ToolCall` that `json.loads`s a string
and validates it into a `ToolCall`, letting `ValidationError` and `json.JSONDecodeError`
propagate as-is.

<details>
<summary>Solution</summary>

```python
import json
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict[str, object]


def parse_tool_call(raw: str) -> ToolCall:
    data = json.loads(raw)
    return ToolCall.model_validate(data)


print(parse_tool_call('{"name": "search_docs", "arguments": {"query": "pydantic"}}'))
# name='search_docs' arguments={'query': 'pydantic'}
```

</details>

## 15. Real-World Challenge

Extend [`examples/structured_llm_output.py`](examples/structured_llm_output.py) so
`parse_llm_json` retries once with a "repair" prompt (simulate it -- no real LLM call needed)
if the first parse raises `ValidationError`, passing the validation errors back into the
(simulated) repair step so a second, corrected JSON string can be validated instead. This is
the real pattern used in production structured-output pipelines when a model's first attempt
doesn't validate.

## 16. Cheat Sheet

```text
PYDANTIC
↓

class Model(BaseModel):              Field(ge=1, le=20)         @field_validator("field")
    field: str = Field(...)          Field(min_length=1)        @classmethod
                                                                 def check(cls, v): ...

Model.model_validate(data)   # parse + validate a dict
instance.model_dump()        # -> dict
instance.model_dump_json()   # -> JSON string

WHEN TO USE
-> validating untrusted data at a boundary (LLM output, API bodies, config)

COMMON MISTAKE
-> using a dataclass where the data actually needs runtime validation

AI USE CASE
-> ExtractedInvoice.model_validate(json.loads(llm_response))  # structured output
```

---

⬅ Back to [main README](../README.md)
