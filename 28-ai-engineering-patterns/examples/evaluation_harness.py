"""Evaluation harness -- run a fixed set of (input, expected) test cases
through a pipeline function and report a pass rate, instead of eyeballing
a handful of outputs manually. This is the same idea as pytest
parametrization (module 19), applied to judging AI pipeline quality
rather than code correctness.

Run: python3 evaluation_harness.py
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


@dataclass
class EvalCase:
    input: str
    expected_contains: str


@dataclass
class EvalResult:
    case: EvalCase
    actual: str
    passed: bool


def run_evaluation(
    pipeline: Callable[[str], str], cases: list[EvalCase]
) -> list[EvalResult]:
    results = []
    for case in cases:
        actual = pipeline(case.input)
        passed = case.expected_contains.lower() in actual.lower()
        results.append(EvalResult(case=case, actual=actual, passed=passed))
    return results


def summarize(results: list[EvalResult]) -> str:
    passed = sum(1 for r in results if r.passed)
    return f"{passed}/{len(results)} passed ({passed / len(results):.0%})"


def classify_sentiment(text: str) -> str:
    """A tiny stand-in "pipeline" being evaluated -- in a real project
    this would call an LLM or a trained classifier."""
    positive_words = {"great", "love", "excellent"}
    return "positive" if positive_words & set(text.lower().split()) else "negative"


if __name__ == "__main__":
    cases = [
        EvalCase(input="I love this library", expected_contains="positive"),
        EvalCase(input="This is great work", expected_contains="positive"),
        EvalCase(input="This is broken and slow", expected_contains="negative"),
        EvalCase(input="Excellent documentation", expected_contains="negative"),  # deliberately wrong
    ]

    results = run_evaluation(classify_sentiment, cases)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] input={result.case.input!r} -> actual={result.actual!r}")

    print(summarize(results))
