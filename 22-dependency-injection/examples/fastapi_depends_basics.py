"""FastAPI's Depends system: a dependency is just a callable; FastAPI
calls it and injects its return value into any endpoint that declares it
as a parameter -- the framework's own built-in DI mechanism.

Requires: fastapi, httpx (see requirements.txt)
Run: python3 fastapi_depends_basics.py
"""
from __future__ import annotations
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


class Settings:
    def __init__(self) -> None:
        self.model_name = "gpt-mini"


def get_settings() -> Settings:
    return Settings()  # in a real app, this might read env vars (module 21)


@app.get("/config")
def read_config(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"model_name": settings.model_name}


if __name__ == "__main__":
    client = TestClient(app)
    response = client.get("/config")
    print(response.json())  # {'model_name': 'gpt-mini'}
