"""AI Engineering Example -- callable Tool objects with their own internal
state (call counts, config), instead of plain functions. __call__ is what
makes `tool(**arguments)` work exactly like calling a function while still
letting the tool carry state and other methods.

Run: python3 callable_tool_registry.py
"""
from __future__ import annotations


class Tool:
    def __init__(self, name: str) -> None:
        self.name = name
        self.call_count = 0

    def run(self, **kwargs: object) -> str:
        raise NotImplementedError

    def __call__(self, **kwargs: object) -> str:
        self.call_count += 1
        return self.run(**kwargs)

    def __repr__(self) -> str:
        return f"<Tool {self.name} calls={self.call_count}>"


class SearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(name="search_docs")

    def run(self, *, query: str, top_k: int = 3) -> str:
        return f"top {top_k} results for {query!r}"


if __name__ == "__main__":
    search = SearchTool()

    print(search(query="advanced oop", top_k=2))  # calling the instance directly
    print(search(query="descriptors"))
    print(search)  # <Tool search_docs calls=2>  -- __repr__ shows tracked state
