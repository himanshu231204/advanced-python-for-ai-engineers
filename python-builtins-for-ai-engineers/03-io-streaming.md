# 03 — I/O & Streaming

Low-level I/O primitives for building custom streaming pipelines, binary protocols, and high-performance data transfer in AI systems.

---

## `io`

**Import:** `import io`

**When to use:** Build in-memory file-like streams for passing data between components that expect file objects (CSV writers, model serializers, HTTP uploads).

**Mental model:** A virtual file that lives in RAM — anything that reads/writes files can read/write this instead, with zero disk I/O.

```python
import io
import json

def serialize_batch_to_jsonl(records: list[dict[str, str]]) -> bytes:
    """Build a JSONL payload in memory for bulk API upload."""
    buffer = io.BytesIO()
    for record in records:
        line = json.dumps(record) + "\n"
        buffer.write(line.encode("utf-8"))
    buffer.seek(0)
    return buffer.read()

training_data = [
    {"prompt": "What is RAG?", "completion": "Retrieval-Augmented Generation..."},
    {"prompt": "Explain embeddings", "completion": "Dense vector representations..."},
]
payload = serialize_batch_to_jsonl(training_data)
print(f"JSONL payload: {len(payload)} bytes")
# Ready to send: requests.post(url, data=payload, headers={"Content-Type": "application/jsonl"})
```

**Gotcha:** Forgetting `buffer.seek(0)` after writing means subsequent reads return empty bytes — the cursor is at the end.

---

## `socket`

**Import:** `import socket`

**When to use:** Health checks, custom protocol clients, or direct TCP communication to inference servers (e.g., TGI, vLLM raw endpoints).

**Mental model:** A telephone line — you dial (connect), talk (send), listen (recv), and hang up (close). The OS handles routing.

```python
import socket
import json

def query_local_inference_server(
    prompt: str, host: str = "127.0.0.1", port: int = 8080
) -> dict[str, str]:
    """Send a raw JSON request to a local inference server over TCP."""
    request = json.dumps({"prompt": prompt, "max_tokens": 100})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        sock.connect((host, port))
        sock.sendall(request.encode("utf-8"))
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    return json.loads(b"".join(chunks).decode("utf-8"))

# result = query_local_inference_server("Summarize this document")
```

**Gotcha:** Always set `settimeout()` — a missing timeout means the socket blocks forever if the server never responds, hanging your entire agent.

---

## `ssl`

**Import:** `import ssl`

**When to use:** Secure connections to self-hosted model endpoints, private vector DBs, or any internal TLS-wrapped service.

**Mental model:** An armored envelope around your socket — same letter inside, but now only the intended recipient can read it.

```python
import ssl
import urllib.request
import json

def fetch_from_private_endpoint(url: str, ca_cert: str) -> dict[str, object]:
    """Hit a TLS-secured internal inference API with a custom CA bundle."""
    ctx = ssl.create_default_context(cafile=ca_cert)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

# response = fetch_from_private_endpoint(
#     "https://internal-llm.corp.net/v1/models",
#     ca_cert="/etc/ssl/corp-ca.pem"
# )
```

**Gotcha:** Disabling `verify_mode` or `check_hostname` in production defeats TLS entirely — never do `ctx.check_hostname = False` outside of local dev.

---

## `struct`

**Import:** `import struct`

**When to use:** Read/write binary embedding files, custom model weight formats, or compact wire protocols for inference servers.

**Mental model:** A cookie cutter for bytes — it stamps raw bytes into Python numbers (and back) using a format template.

```python
import struct
import io

def write_embedding_file(embeddings: list[list[float]], path: str) -> None:
    """Write embeddings to a compact binary format: [count][dim][vectors...]."""
    count = len(embeddings)
    dim = len(embeddings[0])
    with open(path, "wb") as f:
        f.write(struct.pack("<II", count, dim))  # two uint32 header values
        for vec in embeddings:
            f.write(struct.pack(f"<{dim}f", *vec))  # dim float32 values

def read_embedding_header(path: str) -> tuple[int, int]:
    """Read just the header without loading all vectors into memory."""
    with open(path, "rb") as f:
        data = f.read(8)  # 2 x uint32 = 8 bytes
    count, dim = struct.unpack("<II", data)
    return count, dim

# write_embedding_file([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], "/tmp/emb.bin")
# count, dim = read_embedding_header("/tmp/emb.bin")  # (2, 3)
```

**Gotcha:** Byte order matters — `<` is little-endian (most x86), `>` is big-endian (network byte order). Mixing them silently corrupts your data.

---

## `selectors`

**Import:** `import selectors`

**When to use:** Multiplex multiple raw socket connections (e.g., monitoring several inference server health endpoints simultaneously) without threads.

**Mental model:** A switchboard operator — it watches many phone lines at once and tells you which ones are ringing, so one thread can handle them all.

```python
import selectors
import socket

def check_server_health(servers: list[tuple[str, int]]) -> dict[str, bool]:
    """Non-blocking health check across multiple inference servers."""
    sel = selectors.DefaultSelector()
    results: dict[str, bool] = {}

    for host, port in servers:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex((host, port))
        sel.register(sock, selectors.EVENT_WRITE, data=f"{host}:{port}")

    for key, _ in sel.select(timeout=2.0):
        addr = key.data
        sock = key.fileobj
        error = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        results[addr] = error == 0
        sel.unregister(sock)
        sock.close()

    sel.close()
    return results

# health = check_server_health([("127.0.0.1", 8080), ("127.0.0.1", 8081)])
```

**Gotcha:** In practice, prefer `asyncio` for multiplexed I/O. `selectors` is the right tool only when you need raw control below asyncio's abstraction level.
