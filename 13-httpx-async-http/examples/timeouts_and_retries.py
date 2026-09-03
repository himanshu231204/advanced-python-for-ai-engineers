"""HTTP-layer timeouts and a minimal manual retry loop. Real retry logic
(exponential backoff, retryable-vs-not classification) gets its own full
module -- see 15-error-handling-retries -- this is just the HTTPX-specific
pieces: what exception a timeout raises, and where to configure it.

Requires: httpx (see requirements.txt)
Run: python3 timeouts_and_retries.py
"""
from __future__ import annotations
import asyncio
import httpx

attempt_count = 0


def flaky_handler(request: httpx.Request) -> httpx.Response:
    """Simulates a server that's slow the first two times, then succeeds."""
    global attempt_count
    attempt_count += 1
    if attempt_count < 3:
        raise httpx.ConnectTimeout("simulated slow connection", request=request)
    return httpx.Response(200, json={"status": "ok", "attempt": attempt_count})


async def call_with_manual_retry(client: httpx.AsyncClient, *, max_attempts: int) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.get("https://api.example.com/completion")
            return response.json()
        except httpx.TimeoutException as e:
            last_error = e
            print(f"attempt {attempt} timed out")
    assert last_error is not None
    raise last_error


async def main() -> None:
    # A short per-request timeout, configured once at the client level.
    timeout = httpx.Timeout(connect=0.5, read=2.0, write=2.0, pool=2.0)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(flaky_handler), timeout=timeout
    ) as client:
        result = await call_with_manual_retry(client, max_attempts=5)
        print("succeeded:", result)


if __name__ == "__main__":
    asyncio.run(main())
