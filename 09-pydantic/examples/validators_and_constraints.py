"""Field constraints (ge/le/min_length/...) and custom @field_validator
functions for rules a bare type hint can't express.

Requires: pydantic (see requirements.txt)
Run: python3 validators_and_constraints.py
"""
from __future__ import annotations
from pydantic import BaseModel, Field, ValidationError, field_validator


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value.strip()


if __name__ == "__main__":
    print(SearchRequest(query="  async generators  ", top_k=3))
    # query='async generators' top_k=3  <- whitespace stripped by the validator

    for bad_input in [
        {"query": "ok", "top_k": 100},  # violates le=20
        {"query": "   "},  # violates the custom validator
    ]:
        try:
            SearchRequest(**bad_input)
        except ValidationError as e:
            print(f"rejected {bad_input}: {e.errors()[0]['msg']}")
