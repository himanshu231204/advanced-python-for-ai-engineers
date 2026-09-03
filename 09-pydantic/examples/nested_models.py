"""Nested models: a BaseModel field can itself be another BaseModel (or a
list of them) -- Pydantic validates the whole tree, not just the top level.

Requires: pydantic (see requirements.txt)
Run: python3 nested_models.py
"""
from __future__ import annotations
from pydantic import BaseModel, ValidationError


class Citation(BaseModel):
    source: str
    page: int


class Answer(BaseModel):
    text: str
    citations: list[Citation]


if __name__ == "__main__":
    answer = Answer(
        text="Generators are lazy iterators.",
        citations=[{"source": "docs.python.org", "page": 1}, {"source": "pep234", "page": 3}],
    )
    print(answer)
    print(answer.citations[0].source)  # nested dicts become real Citation instances

    try:
        Answer(text="broken", citations=[{"source": "x", "page": "not a number"}])
    except ValidationError as e:
        # the error path tells you exactly which nested field failed
        print(e.errors()[0]["loc"], "->", e.errors()[0]["msg"])
