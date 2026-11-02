# open-parcel

Address lookup for Ottawa parcels: find the parcel and its zone, then explain the zoning bylaw
provisions that apply, with citations. Work is tracked in the GitHub milestones.

Right now the repo is in the M0 exploration phase, so most work happens in notebooks. The
`src/open_parcel/` package is a skeleton of the pipeline interfaces that code moves into as it
stabilises.

## Architecture

The pipeline is `ingest → chunking → index → retrieval → generation → eval`, with small,
stable interfaces between stages. The plan is a simple vector-RAG baseline end to end first,
then hybrid search, graph RAG, agentic retrieval and geo lookup as drop-in retrievers, each
compared on the same question set.

- [docs/architecture.md](docs/architecture.md): stages, interfaces, future plug-ins
- [docs/decisions/](docs/decisions/): why things are the way they are

## Results

Retrieval and answer quality on [`eval/questions.jsonl`](eval/README.md). One row per kept
run; details in [`experiments/`](experiments/README.md).

| Run | Retriever | Chunking | recall@5 | MRR | Notes |
| --- | --------- | -------- | -------- | --- | ----- |

## Layout

```
src/open_parcel/  pipeline package: schemas + one subpackage per stage
configs/          one YAML per experiment (baseline.yaml is the reference)
eval/             labelled question set
experiments/      one folder per run: config, metrics, notes
notebooks/        EDA notebooks (start with 01_ottawa_bylaw_eda.ipynb)
docs/             architecture and decision records
data/             local data, not committed (see below)
legacy/           earlier code kept for reference (Toronto scraper, Postgres/Alembic setup, etc.)
```

## Setup

```bash
uv sync
uv run pre-commit install
uv run jupyter lab
uv run pytest
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
