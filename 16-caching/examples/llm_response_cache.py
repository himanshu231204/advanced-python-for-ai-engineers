"""AI Engineering Example -- caching LLM responses safely. The cache KEY
must include everything that affects the output (prompt, model, and any
sampling parameters) -- leaving one out means two different requests can
collide on the same cached (wrong) answer.

Run: python3 llm_response_cache.py
"""
from __future__ import annotations
import hashlib
import time

_llm_calls = {"count": 0}


def fake_llm_call(prompt: str, *, model: str, temperature: float) -> str:
    _llm_calls["count"] += 1
    return f"[{model}@{temperature}] response to: {prompt}"


def cache_key(prompt: str, *, model: str, temperature: float) -> str:
    """Every parameter that affects the output goes into the key --
    a hash keeps the key short and fixed-length regardless of prompt size."""
    raw = f"{model}|{temperature}|{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


class LLMCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, str]] = {}

    def get_or_call(self, prompt: str, *, model: str, temperature: float) -> str:
        key = cache_key(prompt, model=model, temperature=temperature)
        now = time.monotonic()
        if key in self._store:
            expires_at, value = self._store[key]
            if now < expires_at:
                return value
        value = fake_llm_call(prompt, model=model, temperature=temperature)
        self._store[key] = (now + self.ttl_seconds, value)
        return value


if __name__ == "__main__":
    cache = LLMCache(ttl_seconds=60)

    r1 = cache.get_or_call("summarize this", model="gpt-mini", temperature=0.0)
    r2 = cache.get_or_call("summarize this", model="gpt-mini", temperature=0.0)
    print(r1 == r2, "actual LLM calls so far:", _llm_calls["count"])  # True, 1

    # Different temperature -- a DIFFERENT cache key, correctly NOT reused.
    r3 = cache.get_or_call("summarize this", model="gpt-mini", temperature=0.7)
    print(r3, "actual LLM calls so far:", _llm_calls["count"])  # 2
