"""The same class, written twice, to make the boilerplate `@dataclass`
eliminates concrete instead of abstract.

Run: python3 dataclass_vs_plain_class.py
"""
from __future__ import annotations
from dataclasses import dataclass


class PlainPoint:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"PlainPoint(x={self.x!r}, y={self.y!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlainPoint):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)


@dataclass
class DataclassPoint:
    x: float
    y: float


if __name__ == "__main__":
    a, b = PlainPoint(1, 2), PlainPoint(1, 2)
    c, d = DataclassPoint(1, 2), DataclassPoint(1, 2)

    print(a, a == b)  # PlainPoint(x=1, y=2) True
    print(c, c == d)  # DataclassPoint(x=1, y=2) True
    # Same behavior -- the dataclass version needed zero lines of __init__,
    # __repr__, or __eq__ code.
