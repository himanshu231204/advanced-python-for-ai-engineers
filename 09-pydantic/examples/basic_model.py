"""BaseModel basics: declare fields with type hints, get real runtime
validation for free -- unlike a dataclass (module 08), which only LOOKS
typed.

Requires: pydantic (see requirements.txt)
Run: python3 basic_model.py
"""
from __future__ import annotations
from pydantic import BaseModel, ValidationError


class Point(BaseModel):
    x: float
    y: float


if __name__ == "__main__":
    p = Point(x=1, y=2)  # int -> float coercion happens automatically
    print(p)  # x=1.0 y=2.0
    print(p.model_dump())  # {'x': 1.0, 'y': 2.0}
    print(p.model_dump_json())  # {"x":1.0,"y":2.0}

    try:
        Point(x="not a number", y=2)
    except ValidationError as e:
        print(f"caught {e.error_count()} error(s)")
        print(e.errors()[0]["msg"])
