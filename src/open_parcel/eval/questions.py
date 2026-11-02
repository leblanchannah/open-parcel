"""Loader for the labelled question set in eval/questions.jsonl."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EvalQuestion:
    id: str
    question: str
    # Chunk ids (or section paths) a good retriever should return. Used for recall@k and MRR.
    relevant: list[str]
    # Short reference answer for judging generation. Optional for retrieval-only eval.
    answer: str = ""
    # Free-form labels for slicing results: "definition", "table", "multi-hop", "geo", ...
    tags: list[str] = field(default_factory=list)
    # True for placeholder rows that should not count towards metrics.
    placeholder: bool = False


def load_questions(path: Path, *, include_placeholders: bool = False) -> list[EvalQuestion]:
    questions = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        q = EvalQuestion(**json.loads(line))
        if q.placeholder and not include_placeholders:
            continue
        questions.append(q)
    return questions
