import subprocess
import sys

from demo_pkg.context import format_context


def test_format_context_preserves_input() -> None:
    parts: list[str] = ["First", "", "Second", "First"]
    assert format_context(parts) == "First\n\nSecond\nFirst"
    assert parts == ["First", "", "Second", "First"]


def test_format_context_empty() -> None:
    assert format_context([]) == ""


def test_imports_have_no_output() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import demo_pkg; import demo_pkg.context; import demo_pkg.__main__",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""
    assert result.stderr == ""


def test_package_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "demo_pkg"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == "First\nSecond\n"
    assert result.stderr == ""
