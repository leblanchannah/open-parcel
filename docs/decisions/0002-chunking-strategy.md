# 0002: Chunking strategy

- **Status:** Accepted for the baseline, to be revisited after spot checks
- **Date:** 2026-10-26

## Context

Bylaw questions usually hinge on one provision, one defined term, or one cell of a table.
Chunks that mix several of these dilute embeddings and make citations vague. Chunks that are
too small lose the context needed to answer (for example a table row without its header).

## Decision

1. Start from PyMuPDF `to_chunks` output.
2. **Large or multi-page tables:** one chunk per row, with the table id and header in
   `Chunk.meta`. When a row is retrieved, the full table or page can be fetched later for
   context.
3. **Definitions (s.199):** one chunk per defined term.
4. Every chunk records `section_path`, `kind` and `page_start` / `page_end` so it can be
   cited and so eval can break results down by kind.

## Alternatives considered

- **Fixed-size token windows:** simplest, but split provisions mid-sentence and merge
  unrelated ones.
- **Whole tables as one chunk:** fine for small tables, but large ones exceed sensible chunk
  sizes and one relevant row gets drowned out.

## Consequences

- Row and definition chunks are short, so embeddings may be weak on their own. Adding the
  table header or term name to the chunk text is the first thing to try if recall is low.
- Table rows are expected to cluster together in embedding space; worth checking with a
  visualisation.

## Open questions

- Validate random chunks against page renders.
- Compare `to_chunks` with and without OCR.
- Tune table parameters.
