"""Generation: query + retrieved chunks -> ``Answer`` with citations."""

from collections.abc import Sequence
from typing import Protocol

from open_parcel.schemas import Answer, ScoredChunk


class Generator(Protocol):
    def generate(self, query: str, chunks: Sequence[ScoredChunk]) -> Answer: ...
