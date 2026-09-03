# 21 — Configuration & Environments

**Level:** 2 (Production Python) | **Status:** ✅ Written

API keys, model names, and endpoints must never be hardcoded -- this module covers clean
configuration management across environments, from raw environment variables up to
`pydantic-settings` and safe secret handling.

> Examples in this module need `pydantic-settings` and `python-dotenv`. See
> [`requirements.txt`](requirements.txt).

---

## 1. What is it?

Configuration is anything that varies between environments (dev, staging, production) or
deployments without changing the code itself -- API keys, model names, feature flags,
timeouts. Environment variables are the standard mechanism for passing this into a process;
`.env` files and `pydantic-settings` build convenience and type-safety on top.

## 2. Why does it exist?

Hardcoding an API key or a database URL directly in source code means committing secrets to
version control, and makes it impossible to run the same code against different
environments without editing it. Reading configuration from the environment keeps secrets
out of the codebase and lets the exact same code run correctly in dev, staging, and
production.

## 3. 💡 Mental Model

```text
os.environ / os.getenv  -> raw, untyped strings read directly from the process environment
.env file                -> a local, gitignored file loaded INTO the environment at startup
pydantic-settings         -> typed, validated settings, read from the environment automatically
```

## 4. Syntax

```python
import os

# Raw environment variables (always strings)
value = os.environ["REQUIRED_VAR"]         # KeyError if missing
value = os.getenv("OPTIONAL_VAR", "default")  # never raises

# .env files (local dev convenience)
from dotenv import load_dotenv
load_dotenv(".env")  # reads key=value lines into the process environment

# pydantic-settings -- typed, validated, environment-sourced
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    model_name: str = "gpt-mini"
    temperature: float = 0.0
    api_key: SecretStr  # required -- raises ValidationError if not set

settings = Settings()  # reads MODEL_NAME, TEMPERATURE, API_KEY from the environment
```

## 5. Minimal Example

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_name: str = "gpt-mini"

settings = Settings()
print(settings.model_name)  # "gpt-mini", or whatever MODEL_NAME is set to
```

## 6. What happens internally?

```text
class Settings(BaseSettings):
    model_name: str = "gpt-mini"
    temperature: float = 0.0

Settings()
        │
        ▼
for each field, look up the matching environment variable (by default,
the field name uppercased: MODEL_NAME, TEMPERATURE)
        │
        ▼
if found, parse/coerce the string value to the field's type (like a
regular Pydantic model, module 09) -- "0.7" -> 0.7
        │
        ▼
if not found, fall back to the field's default -- or raise
ValidationError if there is no default and the field is required
```

## 7. Comparison: `os.getenv` vs `pydantic-settings`

| | `os.getenv` | `pydantic-settings` |
|---|---|---|
| Type coercion | manual (`float(os.getenv(...))`) | automatic, like a Pydantic model |
| Validation | none | yes -- required fields raise if missing |
| Secrets handling | plain strings, easy to accidentally log | `SecretStr` masks values in repr/logs |
| Best for | one-off scripts, a couple of variables | a real service's full configuration surface |

## 8. 🎯 AI Engineering Use Case

An AI service's settings need a secret API key that must never leak into logs, plus typed,
validated sampling parameters -- exactly what `pydantic-settings` with `SecretStr` gives you.

### Example A — Tiny

```python
class Settings(BaseSettings):
    model_name: str = "gpt-mini"
```

### Example B — Practical

```python
class Settings(BaseSettings):
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
```

### Example C — AI Engineering

```python
class AIServiceSettings(BaseSettings):
    llm_api_key: SecretStr                              # required, never logged in plain text
    model_name: str = "gpt-mini"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)

settings = AIServiceSettings()
print(settings)  # llm_api_key=SecretStr('**********')
real_key = settings.llm_api_key.get_secret_value()  # explicit opt-in to see it
```

Full runnable version: [`examples/ai_service_settings.py`](examples/ai_service_settings.py)

## 9. WHEN TO USE / WHEN NOT TO

```text
CONFIGURATION MANAGEMENT
✅ Good for:
- anything that varies by environment (API keys, endpoints, model names, timeouts)
- values that must never be committed to source control (secrets)
- a service with more than a couple of configuration values

❌ Avoid when:
- a value never changes and isn't sensitive (a genuine constant belongs in
  code, not as an environment variable nobody will ever actually vary)
- over-engineering a two-variable script with a full Settings class when
  os.getenv would be perfectly clear

BETTER ALTERNATIVE
For a handful of variables in a small script, plain os.getenv is fine.
Reach for pydantic-settings once there's real validation, type coercion,
or secret-handling value to gain.
```

## 10. 🚨 Common Mistakes

**Mistake 1 — hardcoding a secret directly in source code**

```python
# WRONG -- this gets committed to version control, visible to anyone
# with repo access, forever (even if removed later, it's in git history).
API_KEY = "sk-actual-secret-value-here"
```

```python
# BETTER -- read it from the environment, never write the real value in code
class Settings(BaseSettings):
    api_key: SecretStr
```

**Mistake 2 — forgetting environment variables are always strings**

```python
# WRONG -- comparing a string to a bool/int directly does not do what
# you'd expect; os.getenv NEVER returns a bool or number.
if os.getenv("DEBUG"):  # truthy for ANY non-empty string, including "false"!
    ...
```

```python
# BETTER -- convert explicitly, or let pydantic-settings do it for you
debug = os.getenv("DEBUG", "false").lower() == "true"
# or:
class Settings(BaseSettings):
    debug: bool = False  # pydantic-settings correctly parses "true"/"false"/"1"/"0"
```

**Mistake 3 — printing/logging a settings object that includes a plain-string secret**

```python
# WRONG -- a plain `str` field shows its real value in any repr/log output,
# including accidental debug prints or error tracebacks.
class Settings(BaseSettings):
    api_key: str  # leaks in print(settings), logger.info(f"{settings}"), etc.
```

```python
# BETTER -- SecretStr masks the value everywhere except an explicit call
class Settings(BaseSettings):
    api_key: SecretStr

print(settings)  # api_key=SecretStr('**********')
settings.api_key.get_secret_value()  # the only way to see the real value
```

Runnable proof: [`examples/ai_service_settings.py`](examples/ai_service_settings.py)

## 11. ⚡ Quick Tricks

```python
# A default that's used only when the variable is genuinely absent
value = os.getenv("VAR", "default")
```

```python
# Load a .env file for local development
from dotenv import load_dotenv
load_dotenv()
```

```python
# Required, validated, typed settings in one class
class Settings(BaseSettings):
    api_key: SecretStr
    temperature: float = 0.0
```

```python
# Select per-environment behavior from one variable, not scattered checks
if settings.environment == "production":
    ...
```

## 12. Performance Considerations

- Reading environment variables and constructing a `Settings` object is effectively free --
  do it once at startup and pass the resulting object around, rather than re-reading the
  environment on every request.
- `SecretStr`'s masking is purely a repr/string-conversion safeguard -- it adds no meaningful
  runtime cost, so there's no reason not to use it for every sensitive field.

## 13. 🎤 Interview Questions

**Q: Why should API keys and other secrets never be hardcoded in source code?**
A: Hardcoded secrets get committed to version control, remaining visible in git history even
after being "removed" later, and are exposed to anyone with repository access. Reading them
from the environment (backed by a secrets manager or a gitignored `.env` file in local dev)
keeps the actual secret value out of the codebase entirely.

**Q: What's a common bug with treating environment variables as booleans?**
A: `os.getenv("DEBUG")` returns a string or `None` -- never an actual `bool`. Code like `if
os.getenv("DEBUG"):` is truthy for any non-empty string, including `"false"` or `"0"`, which
silently does the opposite of what's intended. The fix is either explicit string comparison
(`.lower() == "true"`) or a typed settings library that parses booleans correctly.

**Q: What does `pydantic_settings.BaseSettings` give you over plain `os.getenv` calls?**
A: The same type coercion and validation as a regular Pydantic model (module 09), applied to
environment variables specifically -- required fields raise a clear error if missing, types
are automatically converted from strings, and (with `SecretStr`) sensitive values are masked
in any repr or log output.

**Q: How would you structure configuration to safely differ between development and
production?**
A: Use one `Settings` shape (so the code always accesses the same typed fields) with an
`environment` field selecting which actual values apply -- either via different `.env`
files/environment variables per deployment, or explicit per-environment override logic --
rather than scattering `if environment == "production":` checks throughout the codebase.

## 14. 🛠 Mini Exercise

Write a `Settings` class (using `pydantic_settings.BaseSettings`) with a required `SecretStr`
field `database_password` and a `pool_size: int` field defaulting to `5`, constrained to
`ge=1, le=100` via `Field`. Confirm it raises when `database_password` isn't set, and that
`pool_size` is properly validated.

<details>
<summary>Solution</summary>

```python
import os
from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_password: SecretStr
    pool_size: int = Field(default=5, ge=1, le=100)


os.environ.pop("DATABASE_PASSWORD", None)
try:
    Settings()
except ValidationError:
    print("raised as expected: database_password is required")

os.environ["DATABASE_PASSWORD"] = "hunter2"
settings = Settings()
print(settings.pool_size)  # 5
print(settings.database_password)  # SecretStr('**********')
```

</details>

## 15. Real-World Challenge

Extend [`examples/per_environment_config.py`](examples/per_environment_config.py) so
`Settings` reads its `environment` field directly from an `ENVIRONMENT` variable (defaulting
to `"development"`) instead of being passed explicitly, and add a `model_config` setting
(`pydantic_settings.SettingsConfigDict(env_file=".env")`) so it also picks up a local `.env`
file automatically when present -- the realistic shape of a service's actual settings module.

## 16. Cheat Sheet

```text
CONFIGURATION & ENVIRONMENTS
↓

os.environ["VAR"]              required, raises KeyError if missing
os.getenv("VAR", "default")    optional, with a fallback

load_dotenv(".env")            load a local .env file into the environment

class Settings(BaseSettings):  typed, validated, environment-sourced config
    api_key: SecretStr             required, masked in repr/logs
    temperature: float = 0.0       optional, type-coerced automatically

WHEN TO USE
-> any real service's configuration surface, especially anything secret or per-environment

COMMON MISTAKE
-> if os.getenv("DEBUG"): -- truthy for ANY non-empty string, including "false"

AI USE CASE
-> AIServiceSettings with a SecretStr API key and validated sampling parameters
```

---

⬅ Back to [main README](../README.md)
