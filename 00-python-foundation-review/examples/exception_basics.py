"""Foundation exception boundaries: local tool arguments and guaranteed cleanup."""

from collections.abc import Callable
from io import StringIO
import json


class ToolArgumentError(ValueError):
    """The caller supplied invalid arguments for the local search tool."""


def parse_limit(raw: str) -> int:
    try:
        limit: int = int(raw)
    except ValueError as exc:
        raise ToolArgumentError("limit must be an integer string") from exc
    if not 1 <= limit <= 10:
        raise ToolArgumentError("limit must be between 1 and 10")
    return limit


def decode_arguments(raw: str) -> tuple[str, int]:
    try:
        arguments: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolArgumentError("search arguments must be valid JSON") from exc
    if not isinstance(arguments, dict):
        raise ToolArgumentError("search arguments must be an object")
    query: object = arguments.get("query")
    limit: object = arguments.get("limit")
    if not isinstance(query, str) or not query.strip():
        raise ToolArgumentError("query must be a non-empty string")
    # bool subclasses int, so an isinstance(limit, int) check would accept True.
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ToolArgumentError("limit must be an integer between 1 and 10")
    return query.strip(), limit


def run_search(raw: str, search: Callable[[str, int], list[str]]) -> list[str]:
    query, limit = decode_arguments(raw)
    return search(query, limit)


def consume_buffer(buffer: StringIO, fail: bool) -> str:
    try:
        if fail:
            raise RuntimeError("processing failed")
        result: str = buffer.read()
    finally:
        buffer.close()
    return result


def main() -> None:
    assert parse_limit("3") == 3
    try:
        parse_limit("many")
    except ToolArgumentError as exc:
        assert isinstance(exc.__cause__, ValueError)
        assert str(exc) == "limit must be an integer string"
    else:
        raise AssertionError("invalid integer accepted")

    assert decode_arguments('{"query": " python ", "limit": 2}') == ("python", 2)
    invalid_inputs: list[str] = [
        "{", "[]", "null", '{"query": "", "limit": 2}',
        '{"query": "python", "limit": true}',
        '{"query": "python", "limit": "2"}',
        '{"query": "python", "limit": 1.5}',
        '{"query": "python", "limit": 0}',
        '{"query": "python", "limit": 11}',
        '{"query": "python"}',
    ]
    for raw in invalid_inputs:
        try:
            decode_arguments(raw)
        except ToolArgumentError as exc:
            assert str(exc)
            if raw == "{":
                assert isinstance(exc.__cause__, json.JSONDecodeError)
        else:
            raise AssertionError(f"invalid input accepted: {raw}")

    def search(query: str, limit: int) -> list[str]:
        return [query] * limit

    assert run_search('{"query": "python", "limit": 2}', search) == ["python", "python"]

    def broken_search(query: str, limit: int) -> list[str]:
        raise RuntimeError(f"index unavailable for {query} ({limit})")

    try:
        run_search('{"query": "python", "limit": 2}', broken_search)
    except RuntimeError as exc:
        assert "index unavailable" in str(exc)
    else:
        raise AssertionError("unexpected search failure was swallowed")

    successful: StringIO = StringIO("local context")
    assert consume_buffer(successful, fail=False) == "local context"
    assert successful.closed
    failing: StringIO = StringIO("local context")
    try:
        consume_buffer(failing, fail=True)
    except RuntimeError as exc:
        assert str(exc) == "processing failed"
    else:
        raise AssertionError("processing failure was swallowed")
    assert failing.closed
    print("Exception basics checks passed.")


if __name__ == "__main__":
    main()
