# 16 — Persistence & Databases

Storing, querying, and managing data that outlives a single process — from SQL databases to key-value stores to document parsing.

---

## `sqlite3`

**Import:** `import sqlite3`

**When to use:** Persistent agent memory store — conversation history, tool results, session state — with zero infrastructure.

**Mental model:** A filing cabinet with SQL superpowers — a single file on disk that supports full relational queries, transactions, and concurrent reads. No server, no setup.

```python
import sqlite3
import json
from datetime import datetime, timezone

class AgentMemory:
    """Persistent agent memory backed by SQLite."""
    def __init__(self, db_path: str = "agent_memory.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session ON memories(session_id)"
        )

    def store(self, session_id: str, role: str, content: str,
              metadata: dict | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO memories (session_id, role, content, metadata) VALUES (?, ?, ?, ?)",
            (session_id, role, content, json.dumps(metadata or {})),
        )
        self.conn.commit()
        return cur.lastrowid

    def recall(self, session_id: str, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT role, content, metadata, created_at FROM memories "
            "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()

memory = AgentMemory("/tmp/agent.db")
memory.store("sess_001", "user", "What is HNSW?")
memory.store("sess_001", "assistant", "HNSW is a graph-based ANN algorithm...",
             metadata={"tokens": 150, "model": "claude-3"})

history = memory.recall("sess_001")
for msg in history:
    print(f"[{msg['role']}] {msg['content'][:50]}...")
memory.close()
```

**Gotcha:** SQLite connections are not thread-safe by default. For multi-threaded agents, use `check_same_thread=False` with a `threading.Lock`, or create one connection per thread.

---

## `shelve`

**Import:** `import shelve`

**When to use:** Quick persistent key-value storage for Python objects — agent configs, cached results, small state that needs to survive restarts.

**Mental model:** A Python dict that saves to disk — you read and write keys like a regular dict, but the data persists between process runs.

```python
import shelve
from typing import Any

class AgentStateStore:
    """Persistent key-value store for agent state between runs."""
    def __init__(self, path: str = "/tmp/agent_state") -> None:
        self.path = path

    def save(self, key: str, value: Any) -> None:
        with shelve.open(self.path) as db:
            db[key] = value

    def load(self, key: str, default: Any = None) -> Any:
        with shelve.open(self.path) as db:
            return db.get(key, default)

    def list_keys(self) -> list[str]:
        with shelve.open(self.path) as db:
            return list(db.keys())

store = AgentStateStore("/tmp/my_agent")
store.save("last_model", "claude-3-opus-20240229")
store.save("conversation_count", 42)
store.save("tool_stats", {"search": 15, "calc": 8, "code": 3})

print(f"Last model: {store.load('last_model')}")
print(f"Conversations: {store.load('conversation_count')}")
print(f"All keys: {store.list_keys()}")
```

**Gotcha:** `shelve` uses `pickle` under the hood — same security risks apply. Never open a shelve file from an untrusted source. Also, mutating a retrieved object doesn't auto-save — reassign the key or use `writeback=True`.

---

## `xml.etree.ElementTree`

**Import:** `import xml.etree.ElementTree as ET`

**When to use:** Parse XML responses from APIs, read configuration files, extract data from web scraping results or SOAP services.

**Mental model:** A tree surgeon — it parses the XML document into a navigable tree of elements, and you can walk, search, or prune any branch.

```python
import xml.etree.ElementTree as ET

def parse_search_api_response(xml_text: str) -> list[dict[str, str]]:
    """Parse XML search results (common in enterprise/SOAP APIs)."""
    root = ET.fromstring(xml_text)
    results: list[dict[str, str]] = []
    for item in root.findall(".//result"):
        results.append({
            "title": item.findtext("title", ""),
            "url": item.findtext("url", ""),
            "snippet": item.findtext("snippet", ""),
        })
    return results

xml_response = """<?xml version="1.0"?>
<search>
    <result>
        <title>RAG Best Practices</title>
        <url>https://example.com/rag</url>
        <snippet>A guide to building production RAG systems...</snippet>
    </result>
    <result>
        <title>Embedding Models Compared</title>
        <url>https://example.com/embeddings</url>
        <snippet>Comparing sentence-transformers, OpenAI, and Cohere...</snippet>
    </result>
</search>"""

results = parse_search_api_response(xml_response)
for r in results:
    print(f"{r['title']}: {r['snippet'][:40]}...")
```

**Gotcha:** `ET.fromstring()` is vulnerable to XML bombs (billion laughs attack) and external entity expansion. For untrusted XML, use `defusedxml` or disable entity expansion.

---

## `html.parser`

**Import:** `from html.parser import HTMLParser`

**When to use:** Strip HTML tags from scraped web content before feeding it to an LLM — clean text extraction without heavy dependencies.

**Mental model:** An HTML tag stripper — it walks through the markup, identifies tags vs. content, and lets you keep just the text.

```python
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    """Extract clean text from HTML for LLM input."""
    SKIP_TAGS = {"script", "style", "head"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._parts.append(text)

    def get_text(self) -> str:
        return " ".join(self._parts)

def html_to_text(html: str) -> str:
    """Convert HTML to clean text for LLM context."""
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()

html = """
<html><head><title>Test</title></head>
<body>
<h1>RAG Pipeline Guide</h1>
<p>This guide covers <strong>chunking</strong>, embedding, and retrieval.</p>
<script>alert("ignored")</script>
</body></html>
"""
print(html_to_text(html))
# RAG Pipeline Guide This guide covers chunking , embedding, and retrieval.
```

**Gotcha:** `HTMLParser` is lenient with malformed HTML but doesn't build a DOM — you can't navigate "up" to a parent element. For complex HTML traversal, use `html.parser` for extraction only.
