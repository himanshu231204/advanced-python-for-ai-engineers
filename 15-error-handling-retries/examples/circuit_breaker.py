"""A minimal circuit breaker: after too many consecutive failures, stop
even TRYING the call for a cooldown period (the "open" state) instead of
retrying a service that's clearly down -- protecting both the caller (fast
failure instead of repeated timeouts) and the struggling downstream service.

Run: python3 circuit_breaker.py
"""
from __future__ import annotations
import time
from enum import Enum, auto


class CircuitState(Enum):
    CLOSED = auto()  # normal operation -- calls go through
    OPEN = auto()  # too many recent failures -- calls are rejected immediately
    HALF_OPEN = auto()  # cooldown elapsed -- let ONE call through to test recovery


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int, cooldown_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None

    def _maybe_recover(self) -> None:
        if (
            self.state is CircuitState.OPEN
            and self.opened_at is not None
            and time.monotonic() - self.opened_at >= self.cooldown_seconds
        ):
            self.state = CircuitState.HALF_OPEN

    def call(self, fn) -> object:
        self._maybe_recover()

        if self.state is CircuitState.OPEN:
            raise CircuitOpenError("circuit is open -- failing fast without calling")

        try:
            result = fn()
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = time.monotonic()
            raise
        else:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            return result


if __name__ == "__main__":
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.2)

    def always_fails() -> None:
        raise RuntimeError("downstream is down")

    for i in range(3):
        try:
            breaker.call(always_fails)
        except RuntimeError:
            print(f"call {i + 1}: failed normally, state={breaker.state.name}")

    try:
        breaker.call(always_fails)
    except CircuitOpenError:
        print(f"call 4: rejected immediately, state={breaker.state.name}")

    time.sleep(0.25)  # let the cooldown elapse

    def now_succeeds() -> str:
        return "recovered"

    print("after cooldown:", breaker.call(now_succeeds), f"state={breaker.state.name}")
