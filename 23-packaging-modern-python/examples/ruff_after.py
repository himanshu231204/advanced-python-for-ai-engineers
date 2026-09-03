"""The same logic, after `ruff check --fix` (removes unused imports/vars)
and `ruff format` (fixes spacing) -- exactly what Ruff produces
automatically from ruff_before.py.

Run: python3 ruff_after.py
"""


def messy(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(messy(2, 3))
