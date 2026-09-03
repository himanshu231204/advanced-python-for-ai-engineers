"""Config discipline -- one validated Settings object, read once at
startup, instead of scattered os.environ[...] calls throughout the
codebase. A missing or malformed variable should fail loudly at startup,
not silently 500 on the first request that happens to need it.

Run: python3 config_discipline.py
"""
from __future__ import annotations
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    max_concurrent_requests: int = Field(default=10, gt=0)


def load_settings_or_exit(**env_overrides: str) -> Settings:
    """Stands in for reading real process environment variables --
    validated ONCE, at startup, instead of trusting every call site to
    read and parse os.environ correctly on its own."""
    try:
        return Settings(**env_overrides)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise SystemExit(f"invalid configuration, refusing to start:\n{exc}") from exc


if __name__ == "__main__":
    settings = load_settings_or_exit(llm_api_key="sk-demo-key")
    print(settings.model_dump())

    try:
        load_settings_or_exit(llm_api_key="sk-demo-key", llm_timeout_seconds="-5")
    except SystemExit as exc:
        print(f"correctly refused bad config: {exc}")
