"""json.dumps/loads: Python's built-in JSON encode/decode. Only a specific
set of types serialize by default -- dict, list, str, int, float, bool,
None -- anything else (datetime, a custom class, bytes) raises TypeError.

Run: python3 json_basics.py
"""
from __future__ import annotations
import json
from datetime import datetime


if __name__ == "__main__":
    data = {"name": "search_docs", "arguments": {"query": "json", "top_k": 3}}

    encoded = json.dumps(data)
    print(encoded)
    print(type(encoded))  # <class 'str'>

    decoded = json.loads(encoded)
    print(decoded == data)  # True -- round-trips cleanly for JSON-native types

    try:
        json.dumps({"created_at": datetime.now()})
    except TypeError as e:
        print(f"caught: {e}")
