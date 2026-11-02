# 0001: PyMuPDF for PDF extraction

- **Status:** Accepted
- **Date:** 2026-10-24

## Context

The Ottawa zoning bylaw is one large PDF with numbered sections, many tables (some spanning
several pages), figures, and a table of contents. Retrieval quality depends on getting
section boundaries, page numbers and table structure out cleanly, because answers must cite
section and page.

## Decision

Use PyMuPDF for text, structure and table extraction.

- `find_tables` works on the bylaw tables with `snap_x_tolerance=10`.
- The TOC gives section structure. The first 16 entries (page -1) are leftover file
  bookmarks and are dropped.

## Alternatives considered

- **pdfplumber**: good table extraction, but slower, and no built-in structured chunk output.
- **OCR-first pipelines**: the PDF has a text layer, so OCR adds cost and errors for little
  gain. Worth one comparison run (see 0002).
- **Hosted document parsers**: extra dependency and cost for a portfolio project, and harder
  to reproduce.

## Consequences

- Page numbers and TOC come for free, which makes citations straightforward.
- Table parameters are tuned to this PDF. A new source document may need its own settings,
  which live in the config (`chunking.table_settings`).
