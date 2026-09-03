"""The context manager protocol: __enter__ and __exit__.

Run: python3 context_manager_protocol.py
"""
from __future__ import annotations
from types import TracebackType


class FileLikeResource:
    """Simulates opening/closing an expensive resource (a DB connection, a
    file handle, a lock) without needing a real file on disk."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.is_open = False

    def __enter__(self) -> "FileLikeResource":
        print(f"opening {self.name}")
        self.is_open = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        print(f"closing {self.name}")
        self.is_open = False
        return False  # False = don't suppress exceptions; let them propagate

    def read(self) -> str:
        if not self.is_open:
            raise RuntimeError("resource is not open")
        return f"data from {self.name}"


if __name__ == "__main__":
    with FileLikeResource("connection.db") as resource:
        print(resource.read())
    print("is_open after block:", resource.is_open)

    # __exit__ still runs even if the block raises.
    try:
        with FileLikeResource("connection2.db"):
            raise ValueError("something went wrong")
    except ValueError as e:
        print(f"caught: {e}")
