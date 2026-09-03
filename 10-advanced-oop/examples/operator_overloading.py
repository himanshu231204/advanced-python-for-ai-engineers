"""Operator overloading: implementing __add__/__eq__/__repr__ lets custom
objects work with +, ==, and print() naturally. Use sparingly -- only when
the operator's meaning is obvious and unsurprising (see When NOT To Use).

Run: python3 operator_overloading.py
"""
from __future__ import annotations


class Vector:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"


if __name__ == "__main__":
    a = Vector(1, 2)
    b = Vector(3, 4)

    print(a + b)  # Vector(4, 6)  -- calls a.__add__(b)
    print(a + b == Vector(4, 6))  # True
