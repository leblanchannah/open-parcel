"""Index: ``Chunk``s -> a searchable store (embeddings, BM25, graph, ...).

Each retrieval technique owns whatever index it needs. An indexer is built once per
config and reused across eval runs.
"""

from collections.abc import Sequence
from typing import Protocol

from open_parcel.schemas import Chunk


class Embedder(Protocol):
    """Turns text into vectors. Swapping embedding models should only touch this."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class Indexer(Protocol):
    def add(self, chunks: Sequence[Chunk]) -> None: ...
