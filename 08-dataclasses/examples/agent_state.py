"""AI Engineering Example -- modeling an agent's internal run state with a
dataclass: cheap to construct, cheap to update, no validation overhead for
data that's already trusted (it's YOUR code producing it, not an LLM or an
external API -- compare to 09-pydantic for untrusted data).

Run: python3 agent_state.py
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Step:
    """One immutable record of a single agent step -- once logged, a past
    step should never be silently mutated."""

    action: str
    result: str


@dataclass(slots=True)
class AgentState:
    goal: str
    steps: list[Step] = field(default_factory=list)
    finished: bool = False

    def record(self, action: str, result: str) -> None:
        self.steps.append(Step(action=action, result=result))

    def finish(self) -> None:
        self.finished = True


if __name__ == "__main__":
    state = AgentState(goal="answer the user's question")
    state.record(action="search_docs", result="found 3 relevant sections")
    state.record(action="summarize", result="drafted an answer")
    state.finish()

    print(state.goal)
    for step in state.steps:
        print(f"  - {step.action}: {step.result}")
    print("finished:", state.finished)
