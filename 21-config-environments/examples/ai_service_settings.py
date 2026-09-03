"""AI Engineering Example -- a real settings shape for an AI service: an
API key that must NEVER leak into logs/reprs (SecretStr), a model name,
sampling parameters, and the current environment, all loaded from the
process environment with validation.

Requires: pydantic-settings (see requirements.txt)
Run: python3 ai_service_settings.py
"""
from __future__ import annotations
import os
from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class AIServiceSettings(BaseSettings):
    environment: Literal["development", "production"] = "development"
    llm_api_key: SecretStr
    model_name: str = "gpt-mini"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_retries: int = Field(default=3, ge=0)


if __name__ == "__main__":
    os.environ["LLM_API_KEY"] = "sk-super-secret-value"
    os.environ["MODEL_NAME"] = "gpt-large"

    settings = AIServiceSettings()

    print(settings)  # llm_api_key shows as SecretStr('**********') -- never the real value
    print(settings.llm_api_key)  # also masked when printed directly

    # The real value is only reachable through an explicit call --
    # exactly the friction you WANT for something this sensitive.
    real_key = settings.llm_api_key.get_secret_value()
    print("actual key starts with:", real_key[:3])
