"""CPython uses reference counting as its primary memory management: an
object is freed the instant its refcount hits zero. Reference CYCLES
(object A refers to B, B refers back to A) can never reach zero refcount
on their own -- that's what the separate cyclic garbage collector (the
`gc` module) exists to clean up.

Run: python3 garbage_collection_basics.py
"""
from __future__ import annotations
import gc
import sys
import weakref


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.other: "Node | None" = None

    def __repr__(self) -> str:
        return f"Node({self.name})"


if __name__ == "__main__":
    a = Node("a")
    # sys.getrefcount includes the temporary reference the call itself
    # creates, so the "true" count is one less than what's printed.
    print("refcount for a:", sys.getrefcount(a) - 1)  # 1 -- only the `a` variable

    b = a
    print("refcount for a after aliasing:", sys.getrefcount(a) - 1)  # 2

    del b
    print("refcount for a after del b:", sys.getrefcount(a) - 1)  # back to 1

    # A reference cycle: n1 -> n2 -> n1. Refcounting alone can't collect this.
    n1, n2 = Node("n1"), Node("n2")
    n1.other = n2
    n2.other = n1

    ref = weakref.ref(n1)  # a weak reference does NOT keep n1 alive
    del n1, n2  # the cycle is now unreachable from anywhere else...
    print("still alive (refcounting can't free a cycle):", ref() is not None)

    gc.collect()  # the cyclic collector finds and frees unreachable cycles
    print("after gc.collect():", ref() is not None)
