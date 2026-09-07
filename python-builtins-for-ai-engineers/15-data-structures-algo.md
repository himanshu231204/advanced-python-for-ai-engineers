# 15 — Data Structures & Algorithms

Specialized data structures for performance-critical paths — priority queues, sorted insertion, typed arrays, and safe copying.

---

## `heapq`

**Import:** `import heapq`

**When to use:** Priority task queue for multi-agent schedulers, top-k retrieval results, any scenario where you always need the "most important" item next.

**Mental model:** A bouncer at a club — always lets the most important task in first. The heap is a cleverly arranged list where the smallest (highest priority) element is always at position 0.

```python
import heapq
import time
from dataclasses import dataclass, field

@dataclass(order=True)
class AgentTask:
    priority: int
    created_at: float = field(compare=False, default_factory=time.time)
    description: str = field(compare=False, default="")
    agent_id: str = field(compare=False, default="")

class MultiAgentScheduler:
    """Priority-based task scheduler for a multi-agent system."""
    def __init__(self) -> None:
        self._queue: list[AgentTask] = []

    def submit(self, task: AgentTask) -> None:
        heapq.heappush(self._queue, task)

    def next_task(self) -> AgentTask | None:
        return heapq.heappop(self._queue) if self._queue else None

    def peek(self) -> AgentTask | None:
        return self._queue[0] if self._queue else None

    @property
    def pending(self) -> int:
        return len(self._queue)

scheduler = MultiAgentScheduler()
scheduler.submit(AgentTask(priority=3, description="Log metrics", agent_id="monitor"))
scheduler.submit(AgentTask(priority=1, description="Answer user", agent_id="chat"))
scheduler.submit(AgentTask(priority=2, description="Fetch context", agent_id="rag"))

while scheduler.pending:
    task = scheduler.next_task()
    print(f"[P{task.priority}] {task.agent_id} → {task.description}")
# [P1] chat → Answer user
# [P2] rag → Fetch context
# [P3] monitor → Log metrics
```

**Gotcha:** `heapq` is a min-heap — smallest value comes first. For max-heap behavior (highest priority first), negate the priority: `heappush(h, (-priority, item))`.

---

## `bisect`

**Import:** `import bisect`

**When to use:** Maintain sorted score lists for leaderboards, binary search on sorted embeddings, efficient threshold-based filtering.

**Mental model:** A librarian who knows exactly where to shelve a new book — instead of scanning every shelf, they jump straight to the right spot using the sorted order.

```python
import bisect

class ScoredResultSet:
    """Maintain a sorted set of (score, item) pairs with efficient insertion."""
    def __init__(self, max_size: int = 100) -> None:
        self._scores: list[float] = []
        self._items: list[str] = []
        self.max_size = max_size

    def insert(self, score: float, item: str) -> None:
        idx = bisect.bisect_left(self._scores, score)
        self._scores.insert(idx, score)
        self._items.insert(idx, item)
        if len(self._scores) > self.max_size:
            self._scores.pop(0)
            self._items.pop(0)

    def top_k(self, k: int) -> list[tuple[float, str]]:
        """Return top-k results (highest scores)."""
        return list(zip(
            reversed(self._scores[-k:]),
            reversed(self._items[-k:]),
        ))

    def above_threshold(self, threshold: float) -> list[tuple[float, str]]:
        """Return all results above a score threshold."""
        idx = bisect.bisect_left(self._scores, threshold)
        return list(zip(self._scores[idx:], self._items[idx:]))

results = ScoredResultSet(max_size=50)
results.insert(0.82, "Doc A: RAG overview")
results.insert(0.95, "Doc B: Embedding guide")
results.insert(0.71, "Doc C: Unrelated topic")
results.insert(0.88, "Doc D: Vector search")

print("Top 2:", results.top_k(2))
print("Above 0.80:", results.above_threshold(0.80))
```

**Gotcha:** `bisect` requires the list to already be sorted. Inserting into an unsorted list produces wrong positions silently — no error, just wrong results.

---

## `array`

**Import:** `from array import array`

**When to use:** Memory-efficient storage for large homogeneous numeric data — embedding components, feature vectors, score arrays — when NumPy isn't available.

**Mental model:** A typed parking lot — every slot is exactly the same size (same type), so it packs tighter than a `list` (which stores pointers to mixed-type objects).

```python
from array import array
import sys

def compare_memory(n: int = 1_000_000) -> dict[str, int]:
    """Show memory savings of array vs list for numeric data."""
    float_list = [0.0] * n
    float_array = array("f", [0.0] * n)  # 'f' = float32, 'd' = float64

    return {
        "list_bytes": sys.getsizeof(float_list),
        "array_bytes": sys.getsizeof(float_array),
        "ratio": round(sys.getsizeof(float_list) / sys.getsizeof(float_array), 1),
    }

def store_scores(scores: list[float]) -> array:
    """Convert float scores to a compact array for batch processing."""
    return array("f", scores)  # float32 — 4 bytes per score instead of ~28

mem = compare_memory()
print(f"List: {mem['list_bytes']:,} bytes")
print(f"Array: {mem['array_bytes']:,} bytes")
print(f"List is {mem['ratio']}x larger")

# Store 10k similarity scores compactly
scores = store_scores([0.1 * (i % 10) for i in range(10_000)])
print(f"Scores array: {len(scores)} items, {sys.getsizeof(scores):,} bytes")
```

**Gotcha:** `array` supports only basic numeric types (`'f'`, `'d'`, `'i'`, `'l'`). For matrix operations, use NumPy — `array` has no vectorized math.

---

## `copy`

**Import:** `from copy import copy, deepcopy`

**When to use:** Clone agent state, conversation history, or config objects before mutation — avoid accidentally modifying the original.

**Mental model:** `copy()` is a photocopy of a page — the text is duplicated but any sticky notes (nested objects) are still shared. `deepcopy()` is a photocopy of the page AND all the sticky notes — fully independent.

```python
from copy import deepcopy
from typing import Any

class ConversationState:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []
        self.metadata: dict[str, Any] = {"tokens": 0, "model": "claude-3"}

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.metadata["tokens"] += len(content.split())

def fork_conversation(state: ConversationState) -> ConversationState:
    """Create an independent fork of a conversation for parallel exploration."""
    return deepcopy(state)

# Original conversation
conv = ConversationState()
conv.add_message("user", "What is RAG?")
conv.add_message("assistant", "RAG is Retrieval-Augmented Generation...")

# Fork for a different exploration path
fork = fork_conversation(conv)
fork.add_message("user", "Give me code examples")

# Original is untouched
print(f"Original: {len(conv.messages)} messages")  # 2
print(f"Fork: {len(fork.messages)} messages")       # 3
```

**Gotcha:** `deepcopy` is slow for large object graphs (it traverses everything recursively). For performance-critical paths, implement `__copy__` / `__deepcopy__` or use structural sharing.
