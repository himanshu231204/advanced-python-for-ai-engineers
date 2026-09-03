"""Dependency injection without any framework: pass dependencies IN
through a constructor/function parameter, instead of a class/function
creating (and hardcoding) its own dependencies internally.

Run: python3 di_without_framework.py
"""
from __future__ import annotations


class RealEmailSender:
    def send(self, to: str, message: str) -> None:
        print(f"[real email] to={to}: {message}")


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))


class NotificationServiceHardcoded:
    """WITHOUT injection -- this class decides its own dependency, so
    tests can't swap it for anything else."""

    def __init__(self) -> None:
        self._sender = RealEmailSender()  # hardcoded -- always the real one

    def notify(self, user: str) -> None:
        self._sender.send(user, "your job is done")


class NotificationService:
    """WITH injection -- the caller decides what `sender` actually is."""

    def __init__(self, sender: RealEmailSender | FakeEmailSender) -> None:
        self._sender = sender

    def notify(self, user: str) -> None:
        self._sender.send(user, "your job is done")


if __name__ == "__main__":
    NotificationServiceHardcoded().notify("alice@example.com")  # always sends "for real"

    fake = FakeEmailSender()
    service = NotificationService(sender=fake)  # inject the fake explicitly
    service.notify("bob@example.com")
    print("captured (no real email sent):", fake.sent)
