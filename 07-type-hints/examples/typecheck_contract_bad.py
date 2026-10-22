"""INTENTIONALLY WRONG: run mypy to diagnose this caller; see the correct module."""
from typecheck_contract import dispatch


def main() -> None:
    print(dispatch({"name": "retrieve", "query": "async Python", "top_k": "3"}))


if __name__ == "__main__":
    main()
