"""A static tool contract; annotations do not validate external input."""
from typing import Literal, TypedDict


class ToolCall(TypedDict):
    name: Literal["retrieve"]
    query: str
    top_k: int


def dispatch(call: ToolCall) -> str:
    return f"{call['name']}: {call['query']} (top_k={call['top_k']})"


def main() -> None:
    print(dispatch({"name": "retrieve", "query": "async Python", "top_k": 3}))


if __name__ == "__main__":
    main()
