"""Config-driven setup -- one validated Settings object, read once at
import time, instead of scattering os.environ reads through the service.
"""
from __future__ import annotations
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = "sk-demo-key"  # a real deployment would require this with no default
    llm_timeout_seconds: float = Field(default=0.5, gt=0)
    cache_ttl_seconds: float = Field(default=60.0, gt=0)


settings = Settings()
