# Exercise 5 — Pydantic Model With No Real Validation

**Category:** Broken Pydantic models

## Symptom

```text
name='support-bot' allowed_roles=[]
```

An `AgentConfig` with an EMPTY list of allowed roles is accepted without complaint -- an
agent that can never actually do anything still passes validation. Run
[`broken.py`](broken.py) and see it for yourself.

## Root Cause

`allowed_roles: list[str] = []` only declares the field's *type* and *default* -- it places
no constraint on what counts as valid. (Note: unlike a plain Python function or a
`dataclasses.dataclass` field, Pydantic v2 does NOT share this default list across
instances -- that specific footgun is already handled. The remaining bug here is purely a
missing business-rule constraint: nothing stops a caller from passing an empty list
explicitly.)

## Fix

Use `Field(min_length=1)` to require at least one role, so Pydantic raises a clear
`ValidationError` for the actually-invalid case instead of silently accepting it. See
[`fixed.py`](fixed.py).

## Takeaway

A type hint on a Pydantic field only constrains its *shape* (it's a list of strings) -- it
says nothing about what makes the *value* valid for your domain. Real business rules (must
be non-empty, must be positive, must match a pattern) need explicit `Field(...)` constraints
or a validator.
