"""Ingest: source documents -> ``Block``s.

Baseline plan: PyMuPDF text and table extraction for the Ottawa bylaw PDF
(see docs/decisions/0001-pymupdf-for-pdf-extraction.md). Exploration lives in
notebooks/01_ottawa_bylaw_eda.ipynb until it stabilises.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from open_parcel.schemas import Block


class Ingestor(Protocol):
    def ingest(self, path: Path) -> Iterator[Block]: ...
