"""The same shape, two ways -- proving the exact difference module 08
promised: a dataclass accepts bad data silently, Pydantic rejects it.

Requires: pydantic (see requirements.txt)
Run: python3 dataclass_vs_pydantic.py
"""
from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel, ValidationError


@dataclass
class PointDC:
    x: float
    y: float


class PointModel(BaseModel):
    x: float
    y: float


if __name__ == "__main__":
    # The dataclass happily accepts obviously wrong data -- no check ever runs.
    bad_dc = PointDC(x="not a number", y="also not a number")
    print(bad_dc)  # PointDC(x='not a number', y='also not a number')

    # The Pydantic model actually validates on construction.
    try:
        PointModel(x="not a number", y="also not a number")
    except ValidationError as e:
        print(f"Pydantic rejected it: {e.error_count()} error(s)")
