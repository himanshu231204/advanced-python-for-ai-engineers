"""Environment variables: the standard way to pass config INTO a process
without hardcoding it in source -- os.environ / os.getenv are the raw,
untyped way to read them.

Run: python3 env_vars_basics.py
"""
from __future__ import annotations
import os


if __name__ == "__main__":
    os.environ["MODEL_NAME"] = "gpt-mini"  # simulating what the shell/deploy env would set

    print(os.environ["MODEL_NAME"])  # KeyError if missing -- use this ONLY when required
    print(os.getenv("TEMPERATURE", "0.0"))  # a default when the variable might not be set
    print(os.getenv("MISSING_VAR"))  # None -- getenv never raises

    # Everything from the environment arrives as a STRING -- you convert it yourself.
    raw_temperature = os.getenv("TEMPERATURE", "0.7")
    temperature = float(raw_temperature)
    print(type(temperature), temperature)  # <class 'float'> 0.7
