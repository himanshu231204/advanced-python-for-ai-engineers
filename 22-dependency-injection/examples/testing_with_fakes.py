"""FastAPI's `app.dependency_overrides` swaps a real dependency for a fake
ONLY for the duration of a test -- the exact same DI mechanism used in
production, repurposed to make tests fast and deterministic.

Requires: fastapi, httpx (see requirements.txt)
Run: python3 testing_with_fakes.py
"""
from __future__ import annotations
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


class LLMClient:
    def complete(self, prompt: str) -> str:
        raise RuntimeError("would call a real, billed API")  # never actually used in this demo


def get_llm_client() -> LLMClient:
    return LLMClient()


@app.get("/complete")
def complete(prompt: str, client: LLMClient = Depends(get_llm_client)) -> dict[str, str]:
    return {"completion": client.complete(prompt)}


class FakeLLMClient(LLMClient):
    def complete(self, prompt: str) -> str:
        return f"[fake] response to: {prompt}"


if __name__ == "__main__":
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient()

    client = TestClient(app)
    response = client.get("/complete", params={"prompt": "hello"})
    print(response.json())  # {'completion': '[fake] response to: hello'} -- no real API call

    app.dependency_overrides.clear()  # restore normal behavior once done
