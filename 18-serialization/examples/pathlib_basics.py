"""pathlib.Path for file handling: object-oriented, cross-platform path
manipulation instead of raw string concatenation with os.path.

Run: python3 pathlib_basics.py
"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data_dir = base / "data"  # `/` joins paths -- no os.path.join needed
        data_dir.mkdir()

        file_path = data_dir / "results.json"
        file_path.write_text(json.dumps({"status": "ok"}))

        print(file_path.exists())  # True
        print(file_path.suffix)  # .json
        print(file_path.stem)  # results
        print(file_path.parent == data_dir)  # True

        loaded = json.loads(file_path.read_text())
        print(loaded)  # {'status': 'ok'}

        print(sorted(p.name for p in base.rglob("*.json")))  # ['results.json']
