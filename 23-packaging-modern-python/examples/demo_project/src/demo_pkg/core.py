"""Core logic for demo_pkg -- lives under src/ so it can only be imported
after the package is actually installed (editable or otherwise), not
accidentally via a stray sys.path entry. This is the main benefit of the
src/ layout over putting the package directly at the project root."""


def summarize_lengths(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}
