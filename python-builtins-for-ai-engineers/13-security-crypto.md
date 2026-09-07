# 13 — Security & Crypto

Secure token generation, message authentication, content integrity — the trust layer for AI systems handling sensitive data.

---

## `hmac`

**Import:** `import hmac`

**When to use:** Verify webhook signatures from LLM providers, sign API payloads, validate that incoming requests haven't been tampered with.

**Mental model:** A tamper-evident seal — the sender signs the message with a shared secret, and the receiver recomputes the seal to confirm nothing was altered in transit.

```python
import hmac
import hashlib
import json
import time

def sign_webhook_payload(payload: dict[str, object], secret: str) -> str:
    """Sign an outgoing webhook payload with HMAC-SHA256."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()

def verify_webhook(
    body: bytes, signature: str, secret: str, max_age_s: int = 300
) -> bool:
    """Verify an incoming webhook's HMAC signature (constant-time comparison)."""
    expected = hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

# Sign an outgoing event
payload = {"event": "eval_complete", "score": 0.94, "timestamp": int(time.time())}
signature = sign_webhook_payload(payload, secret="whsec_abc123")
print(f"Signature: {signature[:16]}...")

# Verify an incoming webhook
body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
is_valid = verify_webhook(body, signature, secret="whsec_abc123")
print(f"Valid: {is_valid}")  # True
```

**Gotcha:** Never compare HMAC signatures with `==` — it's vulnerable to timing attacks. Always use `hmac.compare_digest()` for constant-time comparison.

---

## `secrets`

**Import:** `import secrets`

**When to use:** Generate API keys, session tokens, one-time passwords, and any security-critical random values.

**Mental model:** A casino-grade dice roller — cryptographically secure, unpredictable, and non-reproducible. The only `random` that's safe for security.

```python
import secrets
import hashlib
import string

def generate_api_key(prefix: str = "sk") -> str:
    """Generate a secure API key with a readable prefix."""
    return f"{prefix}_{secrets.token_urlsafe(32)}"

def generate_short_code(length: int = 6) -> str:
    """Generate a human-readable verification code (e.g., for 2FA)."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def hash_api_key(key: str) -> str:
    """Hash an API key for storage — never store keys in plaintext."""
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, iterations=100_000)
    return f"{salt.hex()}:{hashed.hex()}"

# Generate credentials for a new AI service user
api_key = generate_api_key("agent")
verification_code = generate_short_code()
stored_hash = hash_api_key(api_key)

print(f"API Key: {api_key[:15]}...")
print(f"Verification: {verification_code}")
print(f"Stored hash: {stored_hash[:30]}...")
```

**Gotcha:** `secrets.token_urlsafe(n)` generates `n` random bytes, then base64-encodes them — the resulting string is longer than `n` characters. For an exact-length token, use `secrets.token_hex(n // 2)`.

---

## `hashlib` (extended)

**Import:** `import hashlib`

**When to use:** Content-addressable storage for documents, model file integrity verification, deterministic cache keys.

**Mental model:** A fingerprint scanner for data — two identical inputs always produce the same hash, and even a single-bit change produces a completely different one.

```python
import hashlib
from pathlib import Path

def verify_model_file(path: str, expected_sha256: str) -> bool:
    """Verify a downloaded model file's integrity against a known hash."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    return actual == expected_sha256

def content_addressable_key(text: str) -> str:
    """Generate a short, deterministic key for content-addressable storage."""
    return hashlib.blake2b(text.encode(), digest_size=16).hexdigest()

def deduplicate_corpus(documents: list[str]) -> list[str]:
    """Remove exact duplicates from a document corpus using hashing."""
    seen: set[str] = set()
    unique: list[str] = []
    for doc in documents:
        h = content_addressable_key(doc)
        if h not in seen:
            seen.add(h)
            unique.append(doc)
    return unique

# Deduplicate
corpus = ["doc A", "doc B", "doc A", "doc C", "doc B"]
deduped = deduplicate_corpus(corpus)
print(f"Deduped: {len(corpus)} → {len(deduped)}")  # 5 → 3

# Verify file integrity
# valid = verify_model_file("model.bin", "a3f2b7c...")
```

**Gotcha:** SHA-256 is collision-resistant but slow for large volumes. Use `blake2b` for non-cryptographic hashing (dedup, cache keys) — it's faster and built into Python.

---

## `uuid` pattern (extended)

**Import:** `import uuid`

**When to use:** Deterministic IDs from content (uuid5) for idempotent operations, random IDs (uuid4) for tracing, namespace-scoped uniqueness.

**Mental model:** `uuid4` = a random lottery ticket (unique by chance). `uuid5` = a fingerprint derived from input (same input = same ID, always).

```python
import uuid

# Namespace for your AI platform's IDs
AI_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

def deterministic_doc_id(source: str, content: str) -> str:
    """Same document always gets the same ID — idempotent ingestion."""
    return str(uuid.uuid5(AI_NAMESPACE, f"{source}:{content}"))

def random_trace_id() -> str:
    """Unique trace ID for each request — no coordination needed."""
    return uuid.uuid4().hex

# Idempotent: re-ingesting the same doc produces the same ID
id1 = deterministic_doc_id("wiki", "Python is a programming language")
id2 = deterministic_doc_id("wiki", "Python is a programming language")
assert id1 == id2  # always the same

# Random: every trace is unique
trace1 = random_trace_id()
trace2 = random_trace_id()
assert trace1 != trace2
print(f"Deterministic ID: {id1}")
print(f"Random trace: {trace1}")
```

**Gotcha:** `uuid5` uses SHA-1 internally — it's fine for namespace uniqueness but should not be relied on for cryptographic security.
