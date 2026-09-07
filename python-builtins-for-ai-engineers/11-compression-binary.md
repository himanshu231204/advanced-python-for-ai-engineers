# 11 — Compression & Binary

Compressing data, working with archives, and memory-mapping large files — essential for managing model artifacts and large datasets.

---

## `gzip`

**Import:** `import gzip`

**When to use:** Compress/decompress JSONL training data, API request payloads, log files — anything text-heavy that benefits from smaller storage/transfer.

**Mental model:** A vacuum-sealed bag — it squeezes out the redundancy from your data for storage or transfer, then reinflates it on the other end.

```python
import gzip
import json

def compress_training_data(records: list[dict[str, str]], path: str) -> int:
    """Compress training records to gzipped JSONL for storage/upload."""
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    import os
    compressed_size = os.path.getsize(path)
    return compressed_size

def stream_compressed_dataset(path: str):
    """Read a gzipped JSONL dataset line by line — never loads fully into RAM."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

# Write 10k training examples compressed
data = [{"prompt": f"Question {i}", "response": f"Answer {i} " * 50} for i in range(10_000)]
size = compress_training_data(data, "/tmp/training.jsonl.gz")
print(f"Compressed to {size:,} bytes")

# Stream back without loading into memory
count = sum(1 for _ in stream_compressed_dataset("/tmp/training.jsonl.gz"))
print(f"Read back {count} records")
```

**Gotcha:** `gzip.open()` in text mode (`"rt"/"wt"`) handles encoding for you; binary mode (`"rb"/"wb"`) gives raw bytes. Mixing them up causes `TypeError` on write.

---

## `zlib`

**Import:** `import zlib`

**When to use:** In-memory compression for caching — compress cached LLM responses, embeddings, or intermediate results before storing in Redis/memcached.

**Mental model:** The compression engine under the hood — `gzip` wraps files around it, but `zlib` operates directly on bytes for when you need raw speed without file I/O.

```python
import zlib
import json

class CompressedCache:
    """In-memory cache with zlib compression — fits more data in less RAM."""
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def put(self, key: str, value: object) -> int:
        raw = json.dumps(value).encode("utf-8")
        compressed = zlib.compress(raw, level=6)
        self._store[key] = compressed
        return len(compressed)

    def get(self, key: str) -> object | None:
        compressed = self._store.get(key)
        if compressed is None:
            return None
        raw = zlib.decompress(compressed)
        return json.loads(raw.decode("utf-8"))

    @property
    def memory_bytes(self) -> int:
        return sum(len(v) for v in self._store.values())

cache = CompressedCache()
large_response = {"content": "Detailed explanation... " * 200, "tokens": 1500}
compressed_size = cache.put("query:rag-basics", large_response)
print(f"Stored compressed: {compressed_size} bytes")

retrieved = cache.get("query:rag-basics")
print(f"Retrieved content length: {len(retrieved['content'])}")
```

**Gotcha:** `zlib.decompress()` on corrupted data raises `zlib.error` — always wrap in try/except when reading from untrusted sources like caches or network.

---

## `tarfile`

**Import:** `import tarfile`

**When to use:** Package model checkpoints, dataset bundles, or experiment artifacts for storage, transfer, or deployment.

**Mental model:** A shipping container — it bundles multiple files and directories into one unit, optionally compressed, for reliable transport.

```python
import tarfile
from pathlib import Path

def package_model_artifacts(
    model_dir: str, output_path: str
) -> int:
    """Bundle model files into a compressed tarball for deployment."""
    with tarfile.open(output_path, "w:gz") as tar:
        for path in Path(model_dir).rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                arcname = path.relative_to(model_dir)
                tar.add(str(path), arcname=str(arcname))
    return Path(output_path).stat().st_size

def list_archive_contents(archive_path: str) -> list[dict[str, object]]:
    """Inspect a model archive without extracting it."""
    contents: list[dict[str, object]] = []
    with tarfile.open(archive_path, "r:*") as tar:
        for member in tar.getmembers():
            contents.append({
                "name": member.name,
                "size": member.size,
                "is_dir": member.isdir(),
            })
    return contents

# contents = list_archive_contents("model-v2.tar.gz")
# for f in contents:
#     print(f"  {f['name']} ({f['size']} bytes)")
```

**Gotcha:** Never `tar.extractall()` on untrusted archives without filtering — path traversal attacks can overwrite files outside the target directory. Use `tar.extractall(filter="data")` (Python 3.12+).

---

## `zipfile`

**Import:** `import zipfile`

**When to use:** Read/write ZIP files — common format for downloaded datasets (Kaggle), document bundles, and cross-platform artifact exchange.

**Mental model:** A filing cabinet with a directory — unlike tar (which is sequential), zip lets you jump directly to any file inside without reading the others.

```python
import zipfile
import json
from pathlib import Path

def create_eval_bundle(
    results: list[dict[str, object]], report: str, output_path: str
) -> None:
    """Bundle evaluation results and report into a ZIP for sharing."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("results.jsonl", "\n".join(json.dumps(r) for r in results))
        zf.writestr("report.md", report)
        zf.writestr("metadata.json", json.dumps({
            "num_results": len(results),
            "format_version": "1.0",
        }))

def read_dataset_from_zip(zip_path: str, filename: str) -> list[dict[str, str]]:
    """Read a specific file from a downloaded dataset ZIP."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open(filename) as f:
            return [json.loads(line) for line in f]

# create_eval_bundle(
#     results=[{"score": 0.95, "query": "test"}],
#     report="# Eval Report\n\nAll tests passed.",
#     output_path="/tmp/eval_v1.zip",
# )
```

**Gotcha:** `zipfile` does not preserve Unix permissions by default. Extracted scripts lose their execute bit — `chmod +x` after extraction if needed.

---

## `mmap`

**Import:** `import mmap`

**When to use:** Read large embedding binary files or model weight files without loading them entirely into RAM — OS pages in only what you access.

**Mental model:** A window into a file on disk — you slide the window over the file's contents and read through it, but the OS only loads the parts you actually look at.

```python
import mmap
import struct

def read_embedding_by_index(
    path: str, index: int, dim: int = 384
) -> list[float]:
    """Read a single embedding vector from a large binary file via mmap.

    File format: [count: uint32][dim: uint32][vectors: float32 * dim * count]
    """
    header_size = 8  # two uint32 values
    vector_bytes = dim * 4  # float32 = 4 bytes each
    offset = header_size + index * vector_bytes

    with open(path, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        raw = mm[offset:offset + vector_bytes]
        mm.close()

    return list(struct.unpack(f"<{dim}f", raw))

def count_embeddings(path: str) -> int:
    """Read just the header to get embedding count — O(1) regardless of file size."""
    with open(path, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        count = struct.unpack("<I", mm[:4])[0]
        mm.close()
    return count

# With a 10GB embedding file, this uses only ~4KB of RAM:
# vec = read_embedding_by_index("embeddings.bin", index=500_000, dim=384)
# print(f"Vector[500000]: {vec[:5]}...")
```

**Gotcha:** `mmap` on an empty file raises `ValueError`. Always check `os.path.getsize(path) > 0` before mapping. Also, on Windows, you can't resize a mapped file — close the mapping first.
