"""Generic classes with modern PEP 695 syntax (Python 3.12+): `class
Stack[T]:` declares the type parameter directly in the class header --
no `typing.Generic`/`TypeVar` import needed.

Requires: Python 3.12+
Run: python3.12 generic_classes.py
"""
from __future__ import annotations


class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def __len__(self) -> int:
        return len(self._items)


if __name__ == "__main__":
    numbers: Stack[int] = Stack()
    numbers.push(1)
    numbers.push(2)
    print(numbers.pop())  # 2
    print(len(numbers))  # 1

    names: Stack[str] = Stack()
    names.push("alice")
    print(names.pop())  # alice
    # A type checker would reject `names.push(5)` -- `names` is `Stack[str]`
