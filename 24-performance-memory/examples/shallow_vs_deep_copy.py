"""Shallow copy duplicates the OUTER container only -- nested mutable
objects are still shared with the original. Deep copy recursively
duplicates everything, so nothing is shared at any level.

Run: python3 shallow_vs_deep_copy.py
"""
from __future__ import annotations
import copy


if __name__ == "__main__":
    original = {"messages": ["hello"], "config": {"temperature": 0.5}}

    shallow = copy.copy(original)
    shallow["messages"].append("world")  # mutates the SHARED inner list
    print(original["messages"])  # ['hello', 'world'] -- original changed too!
    print(shallow is original)  # False -- different outer dicts
    print(shallow["messages"] is original["messages"])  # True -- same inner list

    original2 = {"messages": ["hello"], "config": {"temperature": 0.5}}
    deep = copy.deepcopy(original2)
    deep["messages"].append("world")
    print(original2["messages"])  # ['hello'] -- untouched
    print(deep["messages"] is original2["messages"])  # False -- fully independent
