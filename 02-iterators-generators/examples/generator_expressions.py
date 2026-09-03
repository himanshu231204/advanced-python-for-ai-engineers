"""Generator expressions vs list comprehensions -- same syntax family,
very different memory behavior.

Run: python3 generator_expressions.py
"""
from __future__ import annotations
import sys


if __name__ == "__main__":
    n = 1_000_000

    list_comp = [i * i for i in range(n)]  # builds the entire list in memory
    gen_expr = (i * i for i in range(n))   # builds nothing yet -- just a generator object

    print("list comprehension size:", sys.getsizeof(list_comp), "bytes")
    print("generator expression size:", sys.getsizeof(gen_expr), "bytes")

    # Both are consumable with the same tools (sum, list, for-loops, ...).
    same_result = sum(x for x in gen_expr if x % 2 == 0) == sum(
        x for x in list_comp if x % 2 == 0
    )
    print("same total:", same_result)

    # ...but a generator can only be consumed ONCE.
    doubled = (i * 2 for i in range(3))
    print(list(doubled))  # [0, 2, 4]
    print(list(doubled))  # []  <- already exhausted, not an error, just empty
