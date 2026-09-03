"""Descriptors: an object with __get__/__set__ controls attribute access on
ANOTHER class. This is the mechanism underneath @property, and a way to
write reusable validated-attribute logic without a full Pydantic model.

Run: python3 descriptors.py
"""
from __future__ import annotations


class PositiveNumber:
    """A reusable descriptor: any attribute using this class enforces
    "must be > 0" without repeating the check in every property."""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = f"_{name}"

    def __get__(self, instance: object, owner: type) -> float:
        return getattr(instance, self._name)

    def __set__(self, instance: object, value: float) -> None:
        if value <= 0:
            raise ValueError(f"expected a positive number, got {value}")
        setattr(instance, self._name, value)


class RateLimiter:
    max_calls_per_minute = PositiveNumber()  # descriptor instance, shared logic

    def __init__(self, max_calls_per_minute: float) -> None:
        self.max_calls_per_minute = max_calls_per_minute  # goes through __set__


if __name__ == "__main__":
    limiter = RateLimiter(max_calls_per_minute=60)
    print(limiter.max_calls_per_minute)  # 60 -- goes through __get__

    try:
        limiter.max_calls_per_minute = -5
    except ValueError as e:
        print(f"caught: {e}")
