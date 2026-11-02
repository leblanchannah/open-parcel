"""Retrieval: query -> ranked ``ScoredChunk``s.

This is the main plug-in point. The baseline is a plain vector retriever; hybrid, graph
and agentic retrievers are later implementations of the same ``Retriever`` protocol, so
eval and generation never need to change when a new technique is added.
"""

from typing import Protocol

from open_parcel.schemas import ScoredChunk


class Retriever(Protocol):
    name: str

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]: ...
