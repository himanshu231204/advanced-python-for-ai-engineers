"""Structured output contract -- define the shape you need from an LLM as
a Pydantic model, and treat a response that fails validation as a
retryable failure, not free-form text to be pattern-matched later. This
turns "the model returned something weird" into "one clear validation
error to retry on."

Run: python3 structured_output_contract.py
"""
from __future__ import annotations
from pydantic import BaseModel, ValidationError


class ExtractedInvoice(BaseModel):
    vendor: str
    total_cents: int
    currency: str


def parse_llm_json(raw_json: str) -> ExtractedInvoice:
    """Stands in for calling an LLM with a JSON-mode/structured-output
    request and validating what comes back."""
    return ExtractedInvoice.model_validate_json(raw_json)


def parse_with_one_retry(attempts: list[str]) -> ExtractedInvoice:
    """Simulates a real pattern: try the first response; if it fails the
    contract, use the (fixed) retry response instead of giving up."""
    last_error: ValidationError | None = None
    for attempt in attempts:
        try:
            return parse_llm_json(attempt)
        except ValidationError as exc:
            last_error = exc
            continue
    assert last_error is not None
    raise last_error


if __name__ == "__main__":
    good_response = '{"vendor": "Acme Corp", "total_cents": 4999, "currency": "USD"}'
    print(parse_llm_json(good_response))

    malformed_first_attempt = '{"vendor": "Acme Corp", "total_cents": "four dollars"}'
    fixed_retry_attempt = '{"vendor": "Acme Corp", "total_cents": 4999, "currency": "USD"}'
    result = parse_with_one_retry([malformed_first_attempt, fixed_retry_attempt])
    print(f"recovered after retry: {result}")

    try:
        parse_llm_json('{"vendor": "Acme Corp"}')
    except ValidationError as exc:
        print(f"rejected incomplete output: {exc.error_count()} error(s)")
