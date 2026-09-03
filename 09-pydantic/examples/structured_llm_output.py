"""AI Engineering Example -- validating structured LLM output before it
touches business logic.

LLM structured output
        ↓
Pydantic validation
        ↓
business logic
        ↓
API response

An LLM asked to return JSON can still return malformed or incomplete data
(hallucinated fields, wrong types, missing keys). Parsing its raw output
straight into a Pydantic model catches that at the boundary, with a clear
error, instead of a confusing crash three functions later.

Requires: pydantic (see requirements.txt)
Run: python3 structured_llm_output.py
"""
from __future__ import annotations
import json
from typing import Literal
from pydantic import BaseModel, ValidationError


class ExtractedInvoice(BaseModel):
    vendor: str
    amount_usd: float
    status: Literal["paid", "unpaid", "overdue"]


def parse_llm_json(raw_json: str) -> ExtractedInvoice:
    """The exact chokepoint: untrusted text in, a validated object out (or
    a clear exception) -- business logic downstream never sees raw LLM text."""
    data = json.loads(raw_json)
    return ExtractedInvoice.model_validate(data)


if __name__ == "__main__":
    good_response = '{"vendor": "Acme Corp", "amount_usd": 199.99, "status": "unpaid"}'
    invoice = parse_llm_json(good_response)
    print(invoice)

    # The model "hallucinated" a status value that isn't one of the three allowed.
    bad_response = '{"vendor": "Acme Corp", "amount_usd": 199.99, "status": "pending review"}'
    try:
        parse_llm_json(bad_response)
    except ValidationError as e:
        print(f"rejected malformed LLM output: {e.errors()[0]['msg']}")
