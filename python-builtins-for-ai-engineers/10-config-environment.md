# 10 — Config & Environment

Reading configuration, parsing CLI flags, and managing environment variables — the startup layer of every AI service.

---

## `configparser`

**Import:** `import configparser`

**When to use:** Read INI-style config files for agent settings — model endpoints, retry policies, feature flags.

**Mental model:** A phonebook for settings — organized into named sections with key-value pairs, readable and editable by humans without touching code.

```python
import configparser
import io

def load_agent_config(config_text: str) -> dict[str, dict[str, str]]:
    """Parse an INI config into a nested dict for agent initialization."""
    parser = configparser.ConfigParser()
    parser.read_string(config_text)
    return {section: dict(parser[section]) for section in parser.sections()}

config_ini = """
[model]
provider = anthropic
name = claude-3-opus-20240229
temperature = 0.7
max_tokens = 4096

[retrieval]
top_k = 10
min_score = 0.75
reranker = cohere

[observability]
log_level = INFO
trace_sampling_rate = 0.1
"""

config = load_agent_config(config_ini)
print(f"Model: {config['model']['name']}")
print(f"Top-K: {config['retrieval']['top_k']}")

# Type conversion (configparser stores everything as strings)
top_k = int(config["retrieval"]["top_k"])
temperature = float(config["model"]["temperature"])
```

**Gotcha:** All values are strings — `configparser` has no native type inference. `config["model"]["max_tokens"]` is `"4096"` (string), not `4096` (int). Always cast explicitly.

---

## `tomllib`

**Import:** `import tomllib`  *(Python 3.11+, read-only)*

**When to use:** Read `pyproject.toml`, tool configs, or any TOML-formatted settings file — the modern config format for Python projects.

**Mental model:** JSON that humans can actually read and write — it supports comments, multi-line strings, and typed values natively.

```python
import tomllib

def load_project_config(path: str = "pyproject.toml") -> dict[str, object]:
    """Load project configuration from a TOML file."""
    with open(path, "rb") as f:
        config = tomllib.load(f)
    return config

# Parse TOML from a string (useful for embedded configs)
toml_str = """
[agent]
name = "research-assistant"
model = "claude-3-opus-20240229"
max_steps = 10
tools = ["web_search", "calculator", "code_interpreter"]

[agent.retry]
max_attempts = 3
backoff_factor = 2.0

[agent.limits]
max_tokens_per_step = 4096
max_total_tokens = 100_000
"""

config = tomllib.loads(toml_str)
print(f"Agent: {config['agent']['name']}")
print(f"Tools: {config['agent']['tools']}")
print(f"Max retries: {config['agent']['retry']['max_attempts']}")

# TOML preserves types — no string casting needed
assert isinstance(config["agent"]["max_steps"], int)
assert isinstance(config["agent"]["retry"]["backoff_factor"], float)
```

**Gotcha:** `tomllib` is read-only — there's no `tomllib.dump()`. To write TOML, use the third-party `tomli-w` package.

---

## `argparse`

**Import:** `import argparse`

**When to use:** Build CLI interfaces for running agents with configurable flags — model selection, verbosity, dry-run mode.

**Mental model:** A front desk receptionist — it takes the raw command-line string, validates the arguments, and hands you a clean namespace of typed values.

```python
import argparse

def build_agent_cli() -> argparse.Namespace:
    """CLI flags for running an agent: --model --verbose --dry-run."""
    parser = argparse.ArgumentParser(
        description="Run an AI agent with configurable settings"
    )
    parser.add_argument(
        "--model", type=str, default="claude-3-opus-20240229",
        help="Model ID for the LLM backend",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.7,
        help="Sampling temperature (0.0 = deterministic)",
    )
    parser.add_argument(
        "--max-steps", type=int, default=10,
        help="Maximum agent reasoning steps",
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Plan steps without executing tools",
    )
    parser.add_argument(
        "--tools", nargs="+", default=["web_search"],
        help="Tools available to the agent",
    )
    return parser.parse_args()

# Usage: python agent.py --model claude-3-haiku -vv --dry-run --tools search calc
# args = build_agent_cli()
# print(f"Model: {args.model}, Verbose: {args.verbose}, Dry run: {args.dry_run}")
```

**Gotcha:** `argparse` calls `sys.exit(2)` on invalid arguments — in tests, wrap the call in a try/except `SystemExit` or use `parser.parse_args([])` with an explicit arg list.

---

## `os.environ` pattern

**Import:** `import os`

**When to use:** Read API keys, model endpoints, feature flags, and deployment config from the environment — the standard for 12-factor apps.

**Mental model:** A global sticky-note board — your deployment platform (Docker, K8s, serverless) posts secrets and config values there, and your code reads them at startup.

```python
import os
from dataclasses import dataclass

@dataclass
class AIServiceConfig:
    """Typed configuration loaded from environment variables."""
    anthropic_api_key: str
    model: str
    max_tokens: int
    temperature: float
    debug: bool
    log_level: str

    @classmethod
    def from_env(cls) -> "AIServiceConfig":
        def require(key: str) -> str:
            val = os.environ.get(key)
            if val is None:
                raise RuntimeError(f"Required env var {key} is not set")
            return val

        return cls(
            anthropic_api_key=require("ANTHROPIC_API_KEY"),
            model=os.environ.get("MODEL", "claude-3-opus-20240229"),
            max_tokens=int(os.environ.get("MAX_TOKENS", "4096")),
            temperature=float(os.environ.get("TEMPERATURE", "0.7")),
            debug=os.environ.get("DEBUG", "false").lower() == "true",
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )

# config = AIServiceConfig.from_env()
# print(f"Using model: {config.model}, debug={config.debug}")
```

**Gotcha:** `os.environ["KEY"]` raises `KeyError` on missing keys; `os.environ.get("KEY")` returns `None`. Always use `.get()` with a default for optional values, and fail fast with a clear message for required ones.
