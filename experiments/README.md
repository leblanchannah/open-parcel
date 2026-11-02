# Experiments

One folder per run, named `YYYY-MM-DD_<config-name>`, for example `2026-11-15_baseline/`.

Each folder holds:

- `config.yaml`: an exact copy of the config used (so the run can be repeated)
- `metrics.json`: the eval output
- `notes.md`: a few lines on what changed, what you expected, and what happened

When a run is worth keeping, add a row to the results table in the top-level README.
Generated artefacts (indexes, embeddings, per-question outputs) stay local and are not
committed.
