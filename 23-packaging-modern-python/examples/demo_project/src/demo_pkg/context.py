"""Pure formatting shared by package callers and its command-line entry point."""


def format_context(parts: list[str]) -> str:
    """Join ranked context parts without modifying their order or contents."""
    return "\n".join(parts)
