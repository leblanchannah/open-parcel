# open-parcel

Address lookup for Ottawa parcels: find the parcel and its zone, then explain the zoning bylaw
provisions that apply, with citations. Work is tracked in the GitHub milestones.

Right now the repo is in the M0 exploration phase, so it is notebook-first.

## Layout

```
notebooks/   EDA notebooks (start with 01_ottawa_bylaw_eda.ipynb)
data/        local data, not committed (see below)
legacy/      earlier code kept for reference (Toronto scraper, Postgres/Alembic setup, etc.)
```

## Setup

```bash
uv sync
uv run pre-commit install
uv run jupyter lab
```

In Jupyter, pick the `open-parcel` / project `.venv` kernel.

## Data

The Ottawa zoning bylaw PDF is too big for git, so `data/` and `*.pdf` are ignored.
Download the bylaw PDF from the City of Ottawa site and save it as:

```
data/raw/ottawa_zoning_bylaw_2026-50.pdf
```

## Notebooks and git

`nbstripout` runs as a pre-commit hook and strips cell outputs before each commit, which keeps
diffs readable and stops large plots or data from landing in git. Your local copy keeps its
outputs. To skip it for one notebook you really want to commit with outputs, add
`"keep_output": true` to that notebook's metadata.

## Chunk viewer

Inspect chunker output with bounding boxes drawn on top of the PDF, and the chunk text
next to it. The list scrolls along with the PDF. Hover a chunk to highlight its boxes, and
click a card or a box to jump to the other one.

```bash
uv run streamlit run chunk_viewer/app.py
```

- Pick a PDF (it defaults to `data/ottawa/2026-050.pdf`, or you can upload one), a page range, and a chunker:
  - **pymupdf4llm** (`to_chunks`): every chunking and boundary-weight param is read from the
    library's own `DEFAULTS` / `WEIGHTS_LAYOUT`
  - **docling** (`HybridChunker`): conversion options plus chunker options. The converted doc is
    cached, so changing chunker params doesn't reconvert the PDF
- **Compare mode** (on by default): pick chunker A and chunker B (e.g. pymupdf4llm vs docling,
  or the same chunker with different params). Each gets its own column with the PDF and its
  boxes on top and its chunk list underneath. The two PDF panes scroll together, and a summary
  table compares chunk counts, token sizes, multi-page chunks, runtime and element kinds.
  Turn the toggle off for the single-chunker view.
- Docling downloads its layout and TableFormer models from Hugging Face on first run.
- Results are cached per (file, pages, params). "Chunks table / export" shows a table and
  saves the run to `data/ottawa/output/viewer_chunks.parquet`.
