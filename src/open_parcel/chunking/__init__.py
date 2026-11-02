"""Chunking: ``Block``s -> ``Chunk``s.

Rules already decided (docs/decisions/0002-chunking-strategy.md):
- PyMuPDF ``to_chunks`` output as the starting point.
- Large or multi-page tables become one chunk per row.
- Definitions (s.199) become one chunk per term.
"""

from collections.abc import Iterable
from typing import Protocol

from open_parcel.schemas import Block, Chunk


class Chunker(Protocol):
    def chunk(self, blocks: Iterable[Block]) -> list[Chunk]: ...
