# demo-pkg

A minimal package demonstrating the modern `src/` layout, used as this module's runnable
example -- see [`../../README.md`](../../README.md) for the full lesson.

```bash
uv sync              # create .venv and install dependencies (from [dependency-groups])
uv run pytest        # run the test suite
uv run ruff check .  # lint
uv run ruff format . # format
```
