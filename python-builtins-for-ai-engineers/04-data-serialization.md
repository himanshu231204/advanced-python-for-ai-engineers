# 04 — Data & Serialization

Converting between Python objects and portable formats — the glue between your AI system's components.

---

## `json`

**Import:** `import json`

**When to use:** Every LLM API speaks JSON — parsing responses, building tool-call payloads, storing structured agent memory.

**Mental model:** The universal translator between Python dicts and the rest of the world — if an API exists, it probably speaks JSON.

```python
import json
from typing import Any

def parse_llm_tool_call(raw_response: str) -> dict[str, Any]:
    """Safely extract structured tool-call data from an LLM response."""
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        return {"error": "LLM returned invalid JSON", "raw": raw_response}

    return {
        "tool": parsed.get("name", "unknown"),
        "args": parsed.get("arguments", {}),
    }

raw = '{"name": "web_search", "arguments": {"query": "RAG best practices"}}'
tool_call = parse_llm_tool_call(raw)
print(tool_call)  # {'tool': 'web_search', 'args': {'query': 'RAG best practices'}}

# Serialize with formatting for debug logs
print(json.dumps(tool_call, indent=2, ensure_ascii=False))
```

**Gotcha:** `json.loads()` happily parses `"true"` and `"null"` into Python `True` and `None`, but `json.dumps()` won't serialize `datetime`, `set`, or `bytes` — add a custom `default` handler or convert first.

---

## `pickle`

**Import:** `import pickle`

**When to use:** Cache expensive Python objects locally — loaded models, preprocessed datasets, fitted tokenizers — between runs.

**Mental model:** Flash-freezing a meal — you preserve the exact Python object (type, state, references) and thaw it later, but only you should eat what you froze (never unpickle untrusted data).

```python
import pickle
import hashlib
from pathlib import Path
from typing import Any

CACHE_DIR = Path("/tmp/agent_cache")
CACHE_DIR.mkdir(exist_ok=True)

def cached_computation(key: str, compute_fn: Any) -> Any:
    """Generic disk cache for expensive Python objects."""
    cache_key = hashlib.sha256(key.encode()).hexdigest()[:16]
    cache_path = CACHE_DIR / f"{cache_key}.pkl"

    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    result = compute_fn()
    with open(cache_path, "wb") as f:
        pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
    return result

# Usage: cache an embedding index between agent restarts
# index = cached_computation("my_index_v2", lambda: build_faiss_index(docs))
```

**Gotcha:** Pickle is a security hole — `pickle.load()` on untrusted data executes arbitrary code. Never unpickle data from user input, APIs, or shared storage without verification.

---

## `csv`

**Import:** `import csv`

**When to use:** Ingest evaluation datasets, export benchmark results, process tabular training data.

**Mental model:** A spreadsheet reader/writer that handles the messy edge cases (commas inside fields, newlines in values, quoting) so you don't have to.

```python
import csv
import io

def parse_eval_dataset(csv_text: str) -> list[dict[str, str]]:
    """Parse an evaluation dataset from CSV into prompt/expected pairs."""
    reader = csv.DictReader(io.StringIO(csv_text))
    return [
        {"prompt": row["prompt"].strip(), "expected": row["expected"].strip()}
        for row in reader
    ]

def write_eval_results(
    results: list[dict[str, str | float]], path: str
) -> None:
    """Write evaluation results to CSV for analysis."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

dataset = parse_eval_dataset("prompt,expected\nWhat is 2+2?,4\nCapital of France?,Paris")
print(f"Loaded {len(dataset)} eval cases")
```

**Gotcha:** Always pass `newline=""` to `open()` when writing CSV — otherwise Python's universal newline translation produces doubled `\r\n` on Windows.

---

## `codecs`

**Import:** `import codecs`

**When to use:** Handle encoding edge cases in multilingual corpora — BOM detection, incremental decoding of streaming byte chunks.

**Mental model:** A universal text adapter — it converts between encodings so your pipeline doesn't choke on a stray UTF-16 BOM or Latin-1 log file.

```python
import codecs

def read_any_encoding(path: str) -> str:
    """Read a text file, auto-detecting BOM for encoding."""
    with open(path, "rb") as f:
        raw = f.read(4)
        f.seek(0)
        if raw.startswith(codecs.BOM_UTF8):
            return f.read().decode("utf-8-sig")
        elif raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            return f.read().decode("utf-16")
        return f.read().decode("utf-8")

def incremental_decode_stream(chunks: list[bytes]) -> str:
    """Decode a stream of byte chunks without splitting multi-byte chars."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    parts: list[str] = []
    for chunk in chunks:
        parts.append(decoder.decode(chunk))
    parts.append(decoder.decode(b"", final=True))
    return "".join(parts)

result = incremental_decode_stream([b"Hello ", b"\xc3\xa9", b"l\xc3\xa8ve"])
print(result)  # Hello élève
```

**Gotcha:** `"utf-8-sig"` strips the BOM on read; plain `"utf-8"` leaves it as a visible `﻿` character at the start of your text, corrupting downstream processing.

---

## `base64`

**Import:** `import base64`

**When to use:** Encode images for multimodal LLM APIs, embed binary data in JSON payloads, handle API auth tokens.

**Mental model:** A text disguise for binary data — it turns raw bytes into safe ASCII characters that survive JSON, HTTP headers, and email without corruption.

```python
import base64
import json

def build_vision_api_payload(image_path: str, prompt: str) -> dict[str, object]:
    """Build a multimodal API request with a base64-encoded image."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    encoded = base64.b64encode(image_bytes).decode("ascii")
    ext = image_path.rsplit(".", 1)[-1].lower()
    media_type = {"png": "image/png", "jpg": "image/jpeg"}.get(ext, "image/png")

    return {
        "model": "claude-3-opus-20240229",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": encoded
                }},
                {"type": "text", "text": prompt},
            ],
        }],
    }

# payload = build_vision_api_payload("screenshot.png", "What's in this image?")
# response = client.messages.create(**payload)
```

**Gotcha:** Base64 inflates size by ~33%. For large files, prefer multipart upload or presigned URLs instead of stuffing megabytes into a JSON payload.
