"""Pytest basics: a test is just a function named `test_*`, using plain
`assert`. Fixtures provide reusable setup (and teardown, via `yield`)
that tests declare as parameters -- pytest wires them up automatically.

Run: python3 -m pytest test_basics_and_fixtures.py -v
"""
from __future__ import annotations
import pytest


def add(a: int, b: int) -> int:
    return a + b


def test_add() -> None:
    assert add(2, 3) == 5


@pytest.fixture
def sample_documents() -> list[str]:
    """A fixture: any test that lists this as a parameter gets this
    return value, freshly computed for that test."""
    return ["doc one", "doc two", "doc three"]


def test_document_count(sample_documents: list[str]) -> None:
    assert len(sample_documents) == 3


@pytest.fixture
def opened_resource():
    """`yield` splits a fixture into setup (before yield) and teardown
    (after yield) -- teardown runs even if the test itself fails."""
    resource = {"open": True}
    yield resource
    resource["open"] = False  # runs after the test, success or failure


def test_resource_is_open_during_test(opened_resource: dict[str, bool]) -> None:
    assert opened_resource["open"] is True
