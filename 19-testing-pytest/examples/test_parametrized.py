"""Parametrized tests: run the SAME test body against many input/output
pairs, instead of copy-pasting near-identical test functions.

Run: python3 -m pytest test_parametrized.py -v
"""
from __future__ import annotations
import pytest

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def is_retryable(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (429, True),
        (500, True),
        (503, True),
        (200, False),
        (400, False),
        (401, False),
    ],
)
def test_is_retryable(status_code: int, expected: bool) -> None:
    assert is_retryable(status_code) is expected


@pytest.mark.parametrize("count", [0, 1, 5])
@pytest.mark.parametrize("prefix", ["a", "b"])
def test_stacked_parametrize_produces_the_cross_product(prefix: str, count: int) -> None:
    """Stacking @parametrize decorators runs the test once per COMBINATION
    -- here, 2 prefixes x 3 counts = 6 total test runs."""
    result = prefix * count
    assert len(result) == len(prefix) * count
