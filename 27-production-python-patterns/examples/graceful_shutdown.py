"""Graceful shutdown -- when a process receives a termination signal, it
should stop accepting NEW work, let IN-FLIGHT work finish (up to a
deadline), then exit. Killing a worker mid-request drops whatever it was
doing; a graceful shutdown drains it first.

Run: python3 graceful_shutdown.py
"""
from __future__ import annotations
import asyncio


class Worker:
    def __init__(self) -> None:
        self._shutting_down = False
        self._in_flight: set[asyncio.Task[None]] = set()

    async def handle_request(self, request_id: str) -> None:
        if self._shutting_down:
            raise RuntimeError(f"rejecting {request_id}: shutting down")
        task = asyncio.current_task()
        assert task is not None
        self._in_flight.add(task)
        try:
            await asyncio.sleep(0.05)  # pretend this is real request work
            print(f"{request_id}: done")
        finally:
            self._in_flight.discard(task)

    async def shutdown(self, drain_timeout: float = 1.0) -> None:
        """Stop taking new work, then wait for whatever is already running."""
        self._shutting_down = True
        if self._in_flight:
            print(f"draining {len(self._in_flight)} in-flight request(s)...")
            await asyncio.wait(self._in_flight, timeout=drain_timeout)
        print("shutdown complete")


async def main() -> None:
    worker = Worker()
    tasks = [asyncio.create_task(worker.handle_request(f"req-{i}")) for i in range(3)]

    await asyncio.sleep(0.01)  # let requests start before the signal arrives
    shutdown_task = asyncio.create_task(worker.shutdown())
    await asyncio.sleep(0)  # yield once so shutdown() actually sets the flag

    try:
        await worker.handle_request("req-late")
    except RuntimeError as exc:
        print(f"rejected: {exc}")

    await asyncio.gather(*tasks)
    await shutdown_task


if __name__ == "__main__":
    asyncio.run(main())
