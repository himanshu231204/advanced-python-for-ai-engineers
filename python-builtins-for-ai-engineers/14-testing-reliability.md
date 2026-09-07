# 14 — Testing & Reliability

Unit testing, mocking, doctests, and debugging — ensuring your AI system works correctly and stays debuggable.

---

## `unittest`

**Import:** `import unittest`

**When to use:** Structured test suites for agent components — tool execution, prompt formatting, response parsing, pipeline steps.

**Mental model:** A quality assurance assembly line — each test is an inspector that checks one specific behavior and shouts if it breaks.

```python
import unittest
from typing import Any

def parse_tool_response(raw: str) -> dict[str, Any]:
    """Parse a tool response, raising ValueError on bad input."""
    import json
    parsed = json.loads(raw)
    if "result" not in parsed:
        raise ValueError("Missing 'result' key in tool response")
    return parsed

class TestToolResponseParser(unittest.TestCase):
    def test_valid_response(self) -> None:
        resp = parse_tool_response('{"result": "42", "source": "calc"}')
        self.assertEqual(resp["result"], "42")

    def test_missing_result_key(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_tool_response('{"data": "no result key"}')
        self.assertIn("Missing 'result'", str(ctx.exception))

    def test_invalid_json(self) -> None:
        with self.assertRaises(Exception):
            parse_tool_response("not json at all")

    def test_nested_result(self) -> None:
        resp = parse_tool_response('{"result": {"items": [1, 2, 3]}}')
        self.assertIsInstance(resp["result"], dict)

if __name__ == "__main__":
    unittest.main()
```

**Gotcha:** `unittest` discovers tests by method name — methods must start with `test_`. A method named `check_response()` silently never runs.

---

## `unittest.mock`

**Import:** `from unittest.mock import AsyncMock, MagicMock, patch`

**When to use:** Mock LLM API clients in tests — avoid real API calls, control responses, verify call patterns.

**Mental model:** A stunt double for your external dependencies — it looks and acts like the real thing, but you control exactly what it does and you can inspect every interaction afterwards.

```python
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass

@dataclass
class Message:
    content: list[dict[str, str]]

@dataclass
class LLMResponse:
    content: list[dict[str, str]]
    usage: dict[str, int]

class Agent:
    def __init__(self, client: object) -> None:
        self.client = client

    async def answer(self, question: str) -> str:
        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0]["text"]

class TestAgent(unittest.IsolatedAsyncioTestCase):
    async def test_answer_calls_api_correctly(self) -> None:
        """Mock AsyncAnthropic client — no real API calls in tests."""
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=LLMResponse(
            content=[{"type": "text", "text": "Paris"}],
            usage={"input_tokens": 10, "output_tokens": 5},
        ))

        agent = Agent(mock_client)
        result = await agent.answer("What is the capital of France?")

        self.assertEqual(result, "Paris")
        mock_client.messages.create.assert_awaited_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "claude-3-opus-20240229")

if __name__ == "__main__":
    unittest.main()
```

**Gotcha:** Use `AsyncMock` for async methods, not `MagicMock` — a regular `MagicMock` returns a `MagicMock` instead of a coroutine, and `await` on it raises `TypeError`.

---

## `doctest`

**Import:** `import doctest`

**When to use:** Inline tests in utility functions — ensures code examples in docstrings stay accurate as the code evolves.

**Mental model:** A REPL session embedded in your docstring — Python runs it and checks that the output matches, so your documentation can never go stale.

```python
def chunk_text(text: str, max_chars: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks for embedding.

    >>> chunk_text("Hello world", max_chars=5, overlap=2)
    ['Hello', 'lo wo', 'world']

    >>> chunk_text("Short", max_chars=100)
    ['Short']

    >>> chunk_text("", max_chars=10)
    []
    """
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        start += max_chars - overlap
        if start >= len(text):
            break
    return chunks

def count_tokens_approx(text: str) -> int:
    """Approximate token count using the ~4 chars/token heuristic.

    >>> count_tokens_approx("Hello world, how are you?")
    6
    >>> count_tokens_approx("")
    0
    """
    if not text:
        return 0
    return max(1, len(text) // 4)

if __name__ == "__main__":
    import doctest
    results = doctest.testmod(verbose=True)
    print(f"\n{results.attempted} tests, {results.failed} failures")
```

**Gotcha:** Doctest compares output literally — whitespace, quote style, and dict ordering all matter. Use `# doctest: +ELLIPSIS` or `# doctest: +NORMALIZE_WHITESPACE` for fuzzy matching.

---

## `pdb` / `breakpoint()`

**Import:** `breakpoint()`  *(no import needed, Python 3.7+)*

**When to use:** Debug agent logic interactively — inspect state mid-pipeline, step through tool selection, examine why a prompt was formatted wrong.

**Mental model:** A pause button for your code — execution freezes at that exact line, and you get a REPL to inspect every variable, step forward, or change values live.

```python
import os

def debug_agent_step(context: dict[str, object], tools: list[str]) -> str:
    """Demonstrate strategic breakpoint placement for debugging."""
    selected_tool = tools[0] if tools else "none"
    prompt = f"Using {selected_tool} with context: {context}"

    # Drop into debugger only in development
    if os.environ.get("DEBUG"):
        breakpoint()
        # In the debugger:
        # p context       — print the context dict
        # p selected_tool — see which tool was picked
        # n               — next line
        # c               — continue execution
        # q               — quit debugger

    return prompt

# Set PYTHONBREAKPOINT=0 to disable all breakpoints in production
# Set PYTHONBREAKPOINT=ipdb.set_trace for a better debugger

# Useful pdb commands for agent debugging:
# p vars()        — see all local variables
# pp expression   — pretty-print complex objects
# w               — show call stack (where am I?)
# u/d             — move up/down the call stack
# l               — list source code around current line
```

**Gotcha:** `breakpoint()` in production hangs the process waiting for input. Set `PYTHONBREAKPOINT=0` in production environments to disable all breakpoints globally.
