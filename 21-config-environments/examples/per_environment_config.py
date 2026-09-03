"""Per-environment configuration: one Settings shape, different actual
values depending on which environment the process is running in --
selected by a single `ENVIRONMENT` variable, not scattered if/else checks.

Requires: pydantic-settings (see requirements.txt)
Run: python3 per_environment_config.py
"""
from __future__ import annotations
import os
from typing import Literal
from pydantic_settings import BaseSettings

Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    environment: Environment = "development"
    model_name: str = "gpt-mini"
    debug: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


def load_settings_for(environment: Environment) -> Settings:
    """Different environments can override different fields -- here just
    debug/model_name, but this is where per-env defaults live."""
    overrides = {
        "development": {"debug": True, "model_name": "gpt-mini"},
        "staging": {"debug": True, "model_name": "gpt-mini"},
        "production": {"debug": False, "model_name": "gpt-large"},
    }[environment]
    return Settings(environment=environment, **overrides)


if __name__ == "__main__":
    for env in ("development", "staging", "production"):
        settings = load_settings_for(env)  # type: ignore[arg-type]
        print(f"{env}: model={settings.model_name}, debug={settings.debug}, "
              f"is_production={settings.is_production}")
