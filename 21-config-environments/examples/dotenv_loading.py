""".env files: keep local development config out of the shell/source and
in one gitignored file, loaded into the process environment at startup.

Requires: python-dotenv (see requirements.txt)
Run: python3 dotenv_loading.py
"""
from __future__ import annotations
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        env_file = Path(tmp) / ".env"
        env_file.write_text("MODEL_NAME=gpt-mini\nTEMPERATURE=0.3\n")

        print("before loading:", os.getenv("MODEL_NAME"))  # None -- not set yet

        load_dotenv(env_file)  # reads the file, sets these as real process env vars

        print("after loading:", os.getenv("MODEL_NAME"))  # gpt-mini
        print("after loading:", os.getenv("TEMPERATURE"))  # 0.3 (still a string!)
