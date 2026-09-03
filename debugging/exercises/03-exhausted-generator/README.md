# Exercise 3 — Exhausted Generator Reused

**Category:** Broken generators

## Symptom

```text
first render: 'Hello world'
second render: ''
```

The second call returns an empty string instead of the same text. Run [`broken.py`](broken.py)
and see it for yourself.

## Root Cause

`token_stream()` is a generator function -- calling it once produces ONE generator object,
which is a single-use iterator. Once `render(tokens)` fully consumes it the first time,
every subsequent iteration attempt (including the second `render(tokens)` call, reusing the
SAME object) immediately finds nothing left to yield.

## Fix

Create a fresh generator for each pass that needs to consume it from the start: call
`token_stream()` again for the second render, rather than reusing the exhausted object. See
[`fixed.py`](fixed.py). (If the same sequence genuinely needs to be iterated many times,
materializing it into a `list` once is the other valid fix.)

## Takeaway

A generator object remembers how far it's been consumed -- it is not "the sequence," it's a
one-time cursor over it. Passing the same generator object to two different consumers means
only the first one actually gets any values.
