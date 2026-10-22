# 07 - Traceback to Breakpoint

**HIGH ROI**: debug a local retrieval adapter without a provider, network, or credentials.

## Symptom

From the repository root (Python 3.12+):

```bash
python debugging/exercises/07-traceback-to-breakpoint/broken.py
```

It logs `INFO ranking retrieval record; score_type=str`, then exits **1**:

```text
TypeError: '>=' not supported between instances of 'str' and 'float'
```

## Root Cause

The adapter supplies `{"score": "0.82"}`. The ranking code assumes a numeric
score and compares the string directly with `0.7`. Read the traceback bottom-up:
`rank_record` contains the failing comparison; `main` supplies the malformed
record; the module frame invokes `main`. These application frames connect the
bad operation to its caller. The log records only the field's type, without
logging retrieved content or a user's prompt.

```text
adapter record -> main -> rank_record -> string >= float -> TypeError
```

## Fix

Normalize once at the adapter boundary. Accept numeric text or numbers, reject
booleans/missing/nonnumeric values, and require a finite score in `[0, 1]`.
`fixed.py` raises a useful `ValueError` for invalid data; it does not silently
replace a corrupt score with zero.

```bash
python debugging/exercises/07-traceback-to-breakpoint/fixed.py
python -m pytest debugging/exercises/07-traceback-to-breakpoint/test_fixed.py -q
```

Expected: script prints `keep`, logs `score_type=str`, exits **0** without stdin;
pytest reports **8 passed**. The tests cover normalization, invalid input, and
normal process termination with a five-second timeout.

### Step-by-step investigation

1. Reproduce the exception above; note the exception class and message.
2. Follow the application frames to the comparison and then the caller.
3. Use the field-type log to test the hypothesis that the score is text.
4. Opt into the debugger explicitly:

   ```bash
   python -m pdb debugging/exercises/07-traceback-to-breakpoint/broken.py
   ```

   At the initial prompt use `b rank_record`, then `c`. At the function use
   `w` to show the stack, `p record`, and `p type(record["score"])`.
   Use `n` to step over lines through the assignment and inspect `p score`.
   Use `c` to reach the exception, then `q` to quit post-mortem debugging.
   `p` evaluates an expression; `w` shows frames; `n` steps within this frame;
   `c` continues to a breakpoint or exception. This command is interactive by
   choice; neither script includes `breakpoint()` or asks for input.
5. Read the fixed boundary check, run its regression test, then try score `"nan"`.

See [logging and observability](../../../20-logging-observability/README.md)
for safe diagnostic context, and the
[foundation review](../../../00-python-foundation-review/README.md) for
traceback/debugger basics.

## Takeaway

A traceback locates the failing operation; locals and safe logs explain why it
failed. Fix the data contract where data enters the system, then preserve the
failure as an automated regression test. Static hints alone cannot normalize
an adapter's external records.
