"""Run with ``python -m demo_pkg`` from an environment containing the package."""

from .context import format_context


def main() -> None:
    print(format_context(["First", "Second"]))


if __name__ == "__main__":
    main()
