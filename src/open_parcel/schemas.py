"""Data passed between pipeline stages.

These types are the contract between stages. Any chunker produces ``Chunk``s, any
retriever returns ``ScoredChunk``s, any generator returns an ``Answer``. Keep them small
and stable: a new technique should be a new implementation, not a new schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ChunkKind(StrEnum):
    """What a chunk represents in the bylaw. Used for filtering and for eval breakdowns."""

    PROVISION = "provision"  # a numbered section or subsection of bylaw text
    DEFINITION = "definition"  # one defined term from s.199
    TABLE_ROW = "table_row"  # one row of a large or multi-page table
    TABLE = "table"  # a small table kept whole
    FIGURE = "figure"  # a figure or its caption


@dataclass(frozen=True, slots=True)
class Block:
    """A raw piece of a source document, as extracted by an ingest step (before chunking)."""

    text: str
    page: int  # 1-based page number in the source PDF
    kind: str = "text"  # text / table / heading / figure, as reported by the extractor
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Chunk:
    """The unit that gets embedded, indexed and retrieved."""

    id: str  # stable across runs, e.g. "s.161(5)" or "table-161#row-12"
    text: str
    section_path: str  # e.g. "Part 6 > Section 161 > (5)"
    kind: ChunkKind
    page_start: int
    page_end: int
    # Anything technique-specific: table id and header for rows, term for definitions,
    # parent section for graph edges, etc. Retrievers may read it; schemas never depend on it.
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    """A chunk returned by a retriever, with its score and which retriever produced it."""

    chunk: Chunk
    score: float  # higher is better; only comparable within one retriever
    source: str = ""  # e.g. "vector", "bm25", "graph", useful once retrievers are combined


@dataclass(frozen=True, slots=True)
class Citation:
    chunk_id: str
    section_path: str
    page_start: int
    page_end: int


@dataclass(frozen=True, slots=True)
class Answer:
    """What the generation stage returns for one query."""

    query: str
    text: str
    citations: list[Citation]
    retrieved: list[ScoredChunk]  # everything the generator saw, kept for eval and debugging
    meta: dict[str, Any] = field(default_factory=dict)  # model, prompt version, latency, ...
