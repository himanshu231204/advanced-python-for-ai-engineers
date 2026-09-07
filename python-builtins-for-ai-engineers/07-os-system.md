# 07 — OS & System

Interacting with the filesystem, processes, and system environment — the operations layer of AI infrastructure.

---

## `os` / `pathlib`

**Import:** `import os` / `from pathlib import Path`

**When to use:** Manage model artifacts, dataset directories, config files, cache paths — any file/directory operation in your AI pipeline.

**Mental model:** `pathlib` is the modern, object-oriented file navigator — it builds paths safely, checks existence, and reads/writes with clean syntax. `os` is the underlying syscall layer you reach for when `pathlib` doesn't cover it.

```python
from pathlib import Path
import os

def setup_agent_workspace(base: str = "agent_workspace") -> dict[str, Path]:
    """Create a structured workspace for an AI agent run."""
    root = Path(base)
    dirs = {
        "models": root / "models",
        "cache": root / "cache" / "embeddings",
        "logs": root / "logs",
        "artifacts": root / "artifacts",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    config_path = root / "config.json"
    if not config_path.exists():
        config_path.write_text('{"model": "claude-3-opus", "temperature": 0.7}')

    # Environment-aware paths
    model_dir = Path(os.environ.get("MODEL_DIR", str(dirs["models"])))
    return {**dirs, "model_dir": model_dir}

workspace = setup_agent_workspace("/tmp/my_agent")
print(f"Cache at: {workspace['cache']}")

# Glob for all cached embedding files
for f in workspace["cache"].glob("*.npy"):
    print(f"Found cached embeddings: {f.name}")
```

**Gotcha:** String concatenation for paths (`dir + "/" + file`) breaks on Windows. Always use `Path / "subpath"` or `os.path.join()`.

---

## `sys`

**Import:** `import sys`

**When to use:** Control the Python runtime — adjust recursion limits for deep agent call trees, inspect platform, manage module paths, access stdin/stdout for CLI agents.

**Mental model:** The control panel for the Python interpreter itself — runtime flags, paths, version info, and the standard streams.

```python
import sys

def check_environment() -> dict[str, str | int]:
    """Validate the runtime environment before starting an agent."""
    info = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "recursion_limit": sys.getrecursionlimit(),
        "max_int_digits": sys.get_int_max_str_digits(),
    }

    if sys.version_info < (3, 12):
        print("WARNING: Python 3.12+ recommended for AI workloads", file=sys.stderr)

    # Increase recursion limit for deeply nested agent call trees
    if sys.getrecursionlimit() < 5000:
        sys.setrecursionlimit(5000)

    return info

def memory_usage_of(obj: object) -> str:
    """Quick memory estimate for an object."""
    size = sys.getsizeof(obj)
    for unit in ["B", "KB", "MB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"

env = check_environment()
print(f"Running on Python {env['python_version']}")
print(f"Size of 1M-item list: {memory_usage_of(list(range(1_000_000)))}")
```

**Gotcha:** `sys.getsizeof()` measures only the object's direct memory, not referenced objects. A list of dicts reports the list container size, not the dict contents. Use `tracemalloc` for deep measurement.

---

## `subprocess`

**Import:** `import subprocess`

**When to use:** Run external tools from your agent — `git`, `docker`, `ffmpeg`, `pandoc`, code interpreters — and capture their output.

**Mental model:** A remote control for other programs — you start them, feed them input, and read their output, all from within Python.

```python
import subprocess
from pathlib import Path

def run_code_interpreter(code: str, timeout: int = 10) -> dict[str, str | int]:
    """Safely execute user-generated code in a subprocess sandbox."""
    result = subprocess.run(
        ["python3", "-c", code],
        capture_output=True,
        text=True,
        timeout=timeout,
        env={"PATH": "/usr/bin"},  # restricted environment
    )
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }

def get_git_context() -> dict[str, str]:
    """Gather git context for an agent working on a codebase."""
    def git(*args: str) -> str:
        r = subprocess.run(["git", *args], capture_output=True, text=True)
        return r.stdout.strip()

    return {
        "branch": git("branch", "--show-current"),
        "last_commit": git("log", "--oneline", "-1"),
        "diff_stat": git("diff", "--stat"),
    }

output = run_code_interpreter("print(2 + 2)")
print(f"Code output: {output['stdout']}")  # 4
```

**Gotcha:** Never use `shell=True` with user-provided input — it enables shell injection. Always pass command and arguments as a list.

---

## `shutil`

**Import:** `import shutil`

**When to use:** High-level file operations — copy model checkpoints, archive experiment results, clean up temporary datasets.

**Mental model:** A moving company for files — it handles the heavy lifting (copy trees, move directories, create archives) that `pathlib` alone can't do.

```python
import shutil
from pathlib import Path
from datetime import datetime

def snapshot_experiment(
    experiment_dir: str, archive_dir: str = "/tmp/experiment_archives"
) -> Path:
    """Archive an experiment's artifacts with a timestamped snapshot."""
    src = Path(experiment_dir)
    dst = Path(archive_dir)
    dst.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{src.name}_{timestamp}"

    archive_path = Path(shutil.make_archive(
        str(dst / archive_name), "gztar", root_dir=str(src.parent), base_dir=src.name
    ))
    print(f"Archived {src} → {archive_path} ({archive_path.stat().st_size} bytes)")
    return archive_path

def cleanup_old_caches(cache_dir: str, max_age_days: int = 7) -> int:
    """Remove cache directories older than max_age_days."""
    import time
    cutoff = time.time() - (max_age_days * 86400)
    removed = 0
    for d in Path(cache_dir).iterdir():
        if d.is_dir() and d.stat().st_mtime < cutoff:
            shutil.rmtree(d)
            removed += 1
    return removed
```

**Gotcha:** `shutil.rmtree()` is irreversible and follows no trash/recycle bin. A typo in the path deletes everything under it immediately.

---

## `tempfile`

**Import:** `import tempfile`

**When to use:** Create temporary files for intermediate processing — downloaded documents, generated code, model artifacts that don't need to persist.

**Mental model:** A scratch pad that self-destructs — you write to it, process it, and the OS cleans it up automatically when you're done.

```python
import tempfile
import json
from pathlib import Path

def process_document_batch(documents: list[dict[str, str]]) -> str:
    """Write docs to a temp JSONL file for batch processing by an external tool."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, prefix="agent_batch_"
    ) as f:
        for doc in documents:
            f.write(json.dumps(doc) + "\n")
        temp_path = f.name

    print(f"Batch written to {temp_path}")
    # External tool processes the file...
    # subprocess.run(["embed-tool", "--input", temp_path])
    return temp_path

def isolated_workspace() -> None:
    """Create an isolated temp directory for one agent run."""
    with tempfile.TemporaryDirectory(prefix="agent_run_") as tmpdir:
        work = Path(tmpdir)
        (work / "input.txt").write_text("user query here")
        (work / "output.json").write_text('{"answer": "42"}')
        print(f"Working in {tmpdir}")
        # ... agent does its work ...
    # Directory and all contents are automatically deleted here

isolated_workspace()
```

**Gotcha:** `delete=False` means *you* are responsible for cleanup — the file persists after the `with` block exits. Orphaned temp files accumulate silently in production.
