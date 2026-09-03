"""Service layering -- separate "what the API looks like" (route) from
"what the business logic does" (service) from "how data is fetched/stored"
(repository). Each layer only knows about the one below it, so any layer
can be tested or swapped independently.

Run: python3 service_layering.py
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Document:
    id: str
    text: str


class DocumentRepository(Protocol):
    """The service layer only depends on THIS shape -- not on any
    particular database or vector store."""

    def get(self, doc_id: str) -> Document | None: ...


class InMemoryDocumentRepository:
    """One concrete implementation -- a real one might wrap Postgres or a
    vector DB, with no changes needed above this layer."""

    def __init__(self) -> None:
        self._docs = {"doc-1": Document(id="doc-1", text="Contextvars isolate async state.")}

    def get(self, doc_id: str) -> Document | None:
        return self._docs.get(doc_id)


class DocumentService:
    """Business logic lives here -- no HTTP concepts, no SQL. Depends only
    on the repository Protocol, so it's trivial to unit test with a fake."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def summarize(self, doc_id: str) -> str:
        doc = self._repository.get(doc_id)
        if doc is None:
            raise ValueError(f"no document with id={doc_id!r}")
        return doc.text[:20] + ("..." if len(doc.text) > 20 else "")


def handle_summarize_request(doc_id: str, service: DocumentService) -> dict[str, str]:
    """Stands in for a route handler -- translates HTTP-shaped input into a
    service call and the result back into a response body."""
    try:
        summary = service.summarize(doc_id)
    except ValueError as exc:
        return {"error": str(exc)}
    return {"doc_id": doc_id, "summary": summary}


if __name__ == "__main__":
    service = DocumentService(InMemoryDocumentRepository())
    print(handle_summarize_request("doc-1", service))
    print(handle_summarize_request("doc-missing", service))
