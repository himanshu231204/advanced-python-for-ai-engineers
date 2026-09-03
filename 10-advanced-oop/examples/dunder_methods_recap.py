"""Combining dunder protocols from earlier modules onto one class: this
resource is simultaneously a context manager (05-context-managers, via
__enter__/__exit__) AND an iterator over its own lines
(02-iterators-generators, via __iter__/__next__). Nothing new syntactically
-- just proof that these protocols are independent and composable on the
same object.

Run: python3 dunder_methods_recap.py
"""
from __future__ import annotations
from types import TracebackType


class InMemoryLog:
    """Pretend "file" backed by a list, so this runs with no real I/O."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self._index = 0
        self._closed = True

    def __enter__(self) -> "InMemoryLog":
        self._closed = False
        print("log opened")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self._closed = True
        print("log closed")
        return False

    def __iter__(self) -> "InMemoryLog":
        return self

    def __next__(self) -> str:
        if self._closed:
            raise RuntimeError("cannot iterate a closed log")
        if self._index >= len(self._lines):
            raise StopIteration
        line = self._lines[self._index]
        self._index += 1
        return line


if __name__ == "__main__":
    with InMemoryLog(["step 1: search", "step 2: summarize"]) as log:
        for line in log:
            print(line)
