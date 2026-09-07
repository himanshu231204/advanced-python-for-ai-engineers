# 12 — Networking & Protocols

HTTP clients, URL handling, email, and unique identifiers — the connectivity layer for AI systems that talk to the outside world.

---

## `http.client`

**Import:** `import http.client`

**When to use:** Low-level HTTP when you can't install `httpx`/`requests` — quick health checks, simple API probes, environments with no third-party packages.

**Mental model:** A manual HTTP typewriter — you type out the request method, headers, and body yourself. Full control, zero magic.

```python
import http.client
import json

def quick_model_health_check(host: str, port: int = 443) -> dict[str, object]:
    """Lightweight health check for an inference endpoint — no deps needed."""
    conn = http.client.HTTPSConnection(host, port, timeout=5)
    try:
        conn.request("GET", "/v1/models", headers={"Accept": "application/json"})
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        return {
            "status": resp.status,
            "healthy": resp.status == 200,
            "models": json.loads(body) if resp.status == 200 else None,
        }
    except (http.client.HTTPException, TimeoutError, OSError) as e:
        return {"status": 0, "healthy": False, "error": str(e)}
    finally:
        conn.close()

# health = quick_model_health_check("api.anthropic.com")
# print(f"API healthy: {health['healthy']}")
```

**Gotcha:** `http.client` doesn't follow redirects automatically — you get a 301/302 response and must handle the redirect yourself. Use `urllib.request` or `httpx` if you need redirect following.

---

## `urllib.parse`

**Import:** `from urllib.parse import urlencode, urlparse, urljoin, quote`

**When to use:** Build API URLs safely — encode query parameters, parse webhook URLs, construct redirect URIs for OAuth flows.

**Mental model:** A URL construction kit — it assembles, disassembles, and sanitizes URLs so special characters don't break your requests.

```python
from urllib.parse import urlencode, urlparse, urljoin, quote

def build_search_api_url(
    base_url: str, query: str, filters: dict[str, str | int]
) -> str:
    """Build a properly encoded search API URL."""
    params = {"q": query, **filters}
    return f"{base_url}?{urlencode(params)}"

def parse_webhook_url(url: str) -> dict[str, str]:
    """Extract components from a webhook callback URL."""
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "path": parsed.path,
        "query": parsed.query,
    }

# Build a search URL with special characters safely encoded
url = build_search_api_url(
    "https://api.search.com/v1/search",
    query="RAG best practices & tips",
    filters={"limit": 10, "source": "docs"},
)
print(url)
# https://api.search.com/v1/search?q=RAG+best+practices+%26+tips&limit=10&source=docs

# Encode a file path for a document API
encoded_path = quote("/documents/my report (final).pdf")
print(f"Encoded: {encoded_path}")
```

**Gotcha:** `urlencode` uses `+` for spaces (form encoding). Some APIs expect `%20` — use `quote(string, safe="")` for those, or pass `quote_via=quote` to `urlencode`.

---

## `smtplib`

**Import:** `import smtplib`

**When to use:** Send alert emails from your AI service — pipeline failures, eval regressions, budget overruns, model drift notifications.

**Mental model:** A post office counter — you hand over the letter (email), the recipient address, and your ID (credentials), and it delivers.

```python
import smtplib
from email.message import EmailMessage

def send_alert(
    subject: str,
    body: str,
    to: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
    sender: str = "alerts@myai.com",
    password: str = "",
) -> bool:
    """Send an alert email when an AI pipeline fails or drifts."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        print(f"Email alert failed: {e}")
        return False

# send_alert(
#     subject="[ALERT] Eval score dropped below threshold",
#     body="Model accuracy fell from 0.92 to 0.81 on the QA benchmark.",
#     to="oncall@team.com",
# )
```

**Gotcha:** Many SMTP servers require app-specific passwords (not your regular login). Gmail, for instance, needs an "App Password" when 2FA is enabled.

---

## `uuid`

**Import:** `import uuid`

**When to use:** Generate unique session IDs, run IDs, trace IDs, and conversation IDs — anything that must be globally unique without coordination.

**Mental model:** A cosmic serial number — so astronomically unlikely to collide that you can generate them independently on different machines and still never get a duplicate.

```python
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class AgentRun:
    """A single agent execution with unique tracing IDs."""
    run_id: str = field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")
    session_id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:12]}")
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    steps: list[dict[str, str]] = field(default_factory=list)

    def add_step(self, tool: str, result: str) -> str:
        step_id = f"step_{uuid.uuid4().hex[:8]}"
        self.steps.append({
            "step_id": step_id,
            "tool": tool,
            "result": result,
            "trace_id": self.trace_id,
        })
        return step_id

run = AgentRun()
run.add_step("web_search", "Found 5 results")
run.add_step("llm_call", "Generated response")
print(f"Run: {run.run_id}")
print(f"Trace: {run.trace_id}")
print(f"Steps: {len(run.steps)}")
```

**Gotcha:** `uuid.uuid4()` is random (128-bit), not sortable by time. If you need time-ordered IDs (e.g., for database keys), use `uuid.uuid7()` (Python 3.14+) or a library like `ulid`.
