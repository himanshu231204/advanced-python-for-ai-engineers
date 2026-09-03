# 18 — Serialization

**Level:** 2 (Production Python) | **Status:** ✅ Written

AI payloads move constantly between JSON, Python objects, and files -- knowing the tradeoffs
keeps data pipelines correct and fast. This module covers the built-in `json` module,
`pathlib` for file handling, and how Pydantic (module 09) solves JSON's most common pitfalls
automatically.

> `pydantic_serialization.py` and `save_and_load_agent_state.py` need the `pydantic` package
> -- see [`09-pydantic/requirements.txt`](../09-pydantic/requirements.txt).

---

## 1. What is it?

Serialization converts an in-memory Python object into a format that can be stored or
transmitted (most commonly JSON text); deserialization reverses it. `pathlib.Path` is
Python's object-oriented API for working with filesystem paths -- reading and writing the
files that serialized data often ends up in.

## 2. Why does it exist?

An LLM API expects JSON in its request body and returns JSON in its response. A saved agent
session, a cached embedding, a config file -- all of these need to move between "a live
Python object" and "bytes on disk or over the network" reliably, without silently losing or
corrupting information along the way.

## 3. 💡 Mental Model

```text
Python object  <---serialize---   JSON text / file
               ---deserialize-->
```

Only a specific set of Python types are "JSON-native" (dict, list, str, int, float, bool,
None) -- anything else (datetime, Enum, bytes, a custom class) needs an explicit conversion
step before it can become JSON.

## 4. Syntax

```python
import json
from pathlib import Path

# JSON encode/decode
text = json.dumps(data)          # Python object -> JSON string
data = json.loads(text)          # JSON string -> Python object
json.dumps(data, default=fn)     # `fn` converts anything json doesn't know how to serialize

# pathlib
path = Path("data") / "results.json"   # `/` joins paths
path.write_text(text)
text = path.read_text()
path.exists() / path.suffix / path.stem / path.parent

# Pydantic (handles most pitfalls automatically -- see 09-pydantic)
model.model_dump()        # -> plain dict
model.model_dump_json()   # -> JSON string, datetimes/Enums included
Model.model_validate_json(text)  # JSON string -> a validated model instance
```

## 5. Minimal Example

```python
import json

data = {"name": "search_docs", "arguments": {"query": "hi"}}
text = json.dumps(data)
print(json.loads(text) == data)  # True
```

## 6. What happens internally?

```text
json.dumps({"created_at": datetime.now()})
        │
        ▼
json's encoder walks the object recursively
        │
        ▼
dict/list/str/int/float/bool/None -> encoded directly
        │
        ▼
a `datetime` isn't any of those -> json has no built-in rule for it
        │
        ▼
raises TypeError, UNLESS a `default=` function was provided to handle
exactly this case
```

## 7. Comparison: `json` module vs Pydantic Serialization

| | `json.dumps`/`loads` | Pydantic `model_dump_json`/`model_validate_json` |
|---|---|---|
| Handles datetime? | no -- needs a custom `default=` | yes, automatically |
| Handles Enum? | only `str`-mixin Enums | yes, automatically |
| Validates on load? | no -- just parses JSON syntax | yes -- validates the resulting data's shape |
| Best for | simple, JSON-native data | structured objects with rich types (dates, enums, nested models) |
| AI use case | quick ad-hoc payloads | saving/loading structured agent state, LLM responses |

## 8. 🎯 AI Engineering Use Case

Persisting an agent's conversation state to disk and reloading it later needs both correct
file handling (`pathlib`) and correct serialization of non-trivial types (timestamps, role
enums) -- exactly what Pydantic handles for free.

### Example A — Tiny

```python
text = json.dumps({"status": "ok"})
```

### Example B — Practical

```python
path = Path("data") / "results.json"
path.write_text(json.dumps(data))
loaded = json.loads(path.read_text())
```

### Example C — AI Engineering

```python
class AgentState(BaseModel):
    session_id: str
    messages: list[Message]

def save_state(state: AgentState, path: Path) -> None:
    path.write_text(state.model_dump_json(indent=2))

def load_state(path: Path) -> AgentState:
    return AgentState.model_validate_json(path.read_text())
```

Full runnable version: [`examples/save_and_load_agent_state.py`](examples/save_and_load_agent_state.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
json module
✅ Use for: simple, JSON-native data with no dates/enums/custom types involved
❌ Avoid when: the data has rich types (datetimes, Enums, nested models) --
   you'll be hand-rolling what Pydantic already does correctly

PYDANTIC SERIALIZATION
✅ Use for: structured objects with dates, enums, nested models; anything
   you also want VALIDATED on the way back in
❌ Avoid when: the data is truly simple and adding a dependency/model
   definition is unnecessary ceremony

BETTER ALTERNATIVE
Reach for Pydantic's serialization the moment datetimes, Enums, or nested
structures enter the picture -- it's what module 09 already gives you.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — trying to `json.dumps` a datetime (or other non-JSON-native type) directly**

```python
# WRONG -- raises TypeError; datetime has no built-in JSON representation.
json.dumps({"created_at": datetime.now()})
```

```python
# BETTER -- convert explicitly, or use Pydantic's model_dump_json which
# does this automatically.
json.dumps({"created_at": datetime.now().isoformat()})
```

Runnable proof: [`examples/serialization_pitfalls.py`](examples/serialization_pitfalls.py)

**Mistake 2 — assuming any Enum serializes to JSON**

```python
# WRONG -- a plain Enum is NOT JSON-serializable, even though its value
# looks like a string.
class Role(Enum):
    USER = "user"

json.dumps({"role": Role.USER})  # TypeError
```

```python
# BETTER -- mix in str so the Enum member genuinely IS a string at
# runtime, or use Pydantic, which serializes any Enum correctly regardless.
class Role(str, Enum):
    USER = "user"

json.dumps({"role": Role.USER})  # works: {"role": "user"}
```

Runnable proof of both the failure and the `str`-mixin fix:
[`examples/serialization_pitfalls.py`](examples/serialization_pitfalls.py)

**Mistake 3 — building file paths with string concatenation instead of `pathlib`**

```python
# WRONG -- fragile across operating systems (Windows uses backslashes),
# and error-prone with missing/extra separators.
path = "data" + "/" + "results.json"
```

```python
# BETTER -- pathlib handles path separators correctly per-platform
from pathlib import Path
path = Path("data") / "results.json"
```

Runnable proof: [`examples/pathlib_basics.py`](examples/pathlib_basics.py)

## 11. ⚡ Quick Tricks

```python
# Join paths with `/` instead of string concatenation
path = Path("data") / "results.json"
```

```python
# Handle any non-JSON-native type with a default function
json.dumps(data, default=lambda v: v.isoformat() if isinstance(v, datetime) else str(v))
```

```python
# Pretty-print JSON for readability
json.dumps(data, indent=2)
```

```python
# Round-trip a Pydantic model through JSON in two calls
text = model.model_dump_json()
restored = Model.model_validate_json(text)
```

## 12. Performance Considerations

- `json.dumps`/`loads` are implemented in C and are fast for JSON-native data -- the
  performance cost of serialization usually comes from custom `default=` functions or
  Pydantic's validation, not the base JSON encoding itself.
- Pydantic v2's serialization core (like its validation core) is written in Rust and fast
  enough for most production use -- prefer it over hand-rolled `default=` functions once
  types get non-trivial, both for correctness and for speed.

## 13. 🎤 Interview Questions

**Q: Why does `json.dumps(datetime.now())` raise an error?**
A: The `json` module's encoder only knows how to serialize a fixed set of JSON-native Python
types (dict, list, str, int, float, bool, None). `datetime` isn't one of them, so without an
explicit conversion (either manually, via `.isoformat()`, or via a `default=` function), the
encoder has no rule for turning it into JSON and raises `TypeError`.

**Q: Why does a plain `Enum` fail to serialize with `json.dumps`, but a `str, Enum` mixin
works?**
A: `json` checks the actual runtime type of each value. A plain `Enum` member's type is the
Enum class itself, not `str`, so it's not JSON-native. A class that inherits from both `str`
and `Enum` produces members that genuinely *are* strings at runtime (in addition to being
Enum members), so `json` serializes them exactly like any other string.

**Q: What advantage does `pathlib.Path` have over building paths with string concatenation
or `os.path.join`?**
A: `Path` objects handle platform-specific separators correctly (`/` vs `\`) via the `/`
operator itself, provide convenient properties (`.suffix`, `.stem`, `.parent`) without manual
string parsing, and offer methods like `.read_text()`/`.write_text()`/`.exists()` directly on
the path object instead of needing separate `open()`/`os.path.exists()` calls.

**Q: Why would you use Pydantic's `model_dump_json`/`model_validate_json` instead of the raw
`json` module for saving agent state to disk?**
A: Agent state typically includes rich types like timestamps and role enums that the `json`
module can't serialize without custom handling. Pydantic handles those automatically, AND
validates the data's shape again on load -- catching corruption or format drift in a saved
file instead of silently loading malformed data.

## 14. 🛠 Mini Exercise

Write `save_json(data: dict, path: Path) -> None` that writes `data` as pretty-printed JSON
(indent=2) to `path`, creating any missing parent directories first, and `load_json(path:
Path) -> dict` that reads it back.

<details>
<summary>Solution</summary>

```python
import json
from pathlib import Path


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


import tempfile

with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "nested" / "data.json"
    save_json({"a": 1}, p)
    print(load_json(p))  # {'a': 1}
```

</details>

## 15. Real-World Challenge

Extend [`examples/save_and_load_agent_state.py`](examples/save_and_load_agent_state.py) so
`save_state` writes to a temporary file first and only renames it over the final path once
the write succeeds (`Path.replace`) -- an atomic-write pattern that avoids leaving a
half-written, corrupted state file if the process crashes mid-write.

## 16. Cheat Sheet

```text
SERIALIZATION
↓

json.dumps(data) / json.loads(text)         JSON-native types only
json.dumps(data, default=fn)                 handle datetime/bytes/custom types

Path("a") / "b.json"                         join paths
path.read_text() / path.write_text(text)     file I/O
path.exists() / .suffix / .stem / .parent    path inspection

model.model_dump_json()                      Pydantic: handles dates/enums automatically
Model.model_validate_json(text)              ...and validates on the way back in

WHEN TO USE
-> json for simple JSON-native data; Pydantic once dates/enums/nested models appear

COMMON MISTAKE
-> json.dumps(datetime.now()) -- TypeError, no built-in JSON rule for datetime

AI USE CASE
-> AgentState.model_validate_json(path.read_text())  # reload saved agent session state
```

---

⬅ Back to [main README](../README.md)
