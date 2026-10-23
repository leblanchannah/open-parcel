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
