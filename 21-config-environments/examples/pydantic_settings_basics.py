"""pydantic-settings: a BaseSettings class reads environment variables
automatically, with the SAME type coercion and validation as a regular
Pydantic BaseModel (module 09) -- no manual os.getenv + type conversion.

Requires: pydantic-settings (see requirements.txt)
Run: python3 pydantic_settings_basics.py
"""
from __future__ import annotations
import os
from pydantic import ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_name: str = "gpt-mini"  # env var MODEL_NAME (case-insensitive by default)
    temperature: float = 0.0  # automatically parsed from the string env var
    max_retries: int = 3


if __name__ == "__main__":
    # With nothing set, every field falls back to its default.
    print(Settings())

    os.environ["MODEL_NAME"] = "gpt-large"
    os.environ["TEMPERATURE"] = "0.7"  # a STRING in the environment...
    settings = Settings()
    print(settings)
    print(type(settings.temperature))  # <class 'float'> -- coerced automatically

    # Required fields with no default raise a real ValidationError if missing.
    class RequiresApiKey(BaseSettings):
        api_key: str  # no default -- REQUIRED

    os.environ.pop("API_KEY", None)
    try:
        RequiresApiKey()
    except ValidationError as e:
        print(f"caught: {e.errors()[0]['msg']}")
