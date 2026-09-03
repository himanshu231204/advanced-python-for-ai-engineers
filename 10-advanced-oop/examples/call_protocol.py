"""__call__ makes any instance callable like a function -- this is exactly
how a class-based decorator (module 06) and a callable "tool" object work.

Run: python3 call_protocol.py
"""
from __future__ import annotations


class Multiplier:
    def __init__(self, factor: int) -> None:
        self.factor = factor

    def __call__(self, value: int) -> int:
        return value * self.factor


if __name__ == "__main__":
    double = Multiplier(2)
    triple = Multiplier(3)

    print(double(5))  # 10 -- `double(5)` is sugar for `double.__call__(5)`
    print(triple(5))  # 15

    print(callable(double))  # True -- `callable()` checks for __call__
    print(callable(42))  # False
