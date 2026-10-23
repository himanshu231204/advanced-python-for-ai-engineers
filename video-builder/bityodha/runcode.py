"""Slice real example files and run them to capture genuine output."""
import subprocess
import sys
from pathlib import Path


class RunError(RuntimeError):
    pass


def slice_lines(path: Path, lines: tuple[int, int]) -> str:
    start, end = lines
    return "\n".join(path.read_text().splitlines()[start - 1 : end])


def run_example(path: Path, timeout: float = 30) -> str:
    try:
        proc = subprocess.run(
            [sys.executable, "-I", str(path)],
            cwd=path.parent,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RunError(f"{path.name}: timed out after {timeout}s") from exc
    if proc.returncode != 0:
        raise RunError(f"{path.name}: exit {proc.returncode}\n{proc.stderr.strip()}")
    out = proc.stdout.strip()
    if not out:
        raise RunError(f"{path.name}: produced no output")
    return out
