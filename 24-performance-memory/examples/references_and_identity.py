"""Every Python variable is a reference to an object, not a box holding a
value directly. Assignment copies the REFERENCE, not the object -- `is`
checks whether two references point to the SAME object; `==` checks
whether the objects are considered equal.

Run: python3 references_and_identity.py
"""
from __future__ import annotations


if __name__ == "__main__":
    a = [1, 2, 3]
    b = a  # `b` now refers to the SAME list object as `a` -- no copy happened

    b.append(4)
    print(a)  # [1, 2, 3, 4] -- mutating `b` also changed what `a` sees
    print(a is b)  # True -- same object
    print(id(a) == id(b))  # True -- `is` compares exactly this

    c = [1, 2, 3, 4]
    print(a == c)  # True -- equal VALUES
    print(a is c)  # False -- different objects, same content

    # Small integers (-5 to 256) are cached by CPython, so `is` "accidentally"
    # works for them -- an implementation detail, never something to rely on.
    x, y = 100, 100
    print(x is y)  # True -- both are the same cached small-int object

    # Build these at runtime (not as literals) so the compiler can't fold
    # them into one shared constant -- this is the honest, general case.
    values = [20_000, 5_000]
    big1 = values[0] - values[1]
    big2 = values[0] - values[1]
    print(big1 == big2, big1 is big2)  # True, False -- equal value, different objects
