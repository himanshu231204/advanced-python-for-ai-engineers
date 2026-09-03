"""@dataclass basics: generates __init__, __repr__, and __eq__ from
annotated class attributes -- no boilerplate.

Run: python3 basic_dataclass.py
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Point:
    x: float
    y: float


if __name__ == "__main__":
    a = Point(1.0, 2.0)
    b = Point(1.0, 2.0)

    print(a)  # Point(x=1.0, y=2.0)  <- __repr__ generated for free
    print(a == b)  # True  <- __eq__ compares field values, not identity
    print(a is b)  # False -- still two different objects
