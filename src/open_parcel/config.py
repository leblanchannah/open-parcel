"""Experiment config: one YAML file in configs/ describes one pipeline run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> dict[str, Any]:
    """Load a run config. Kept as a plain dict until the stage options settle."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
