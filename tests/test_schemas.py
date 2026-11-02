from pathlib import Path

from open_parcel.eval import load_questions
from open_parcel.schemas import Chunk, ChunkKind, ScoredChunk

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_chunk_roundtrip() -> None:
    chunk = Chunk(
        id="s.199/lot-line-front",
        text="Lot line, front means ...",
        section_path="Section 199",
        kind=ChunkKind.DEFINITION,
        page_start=1,
        page_end=1,
    )
    scored = ScoredChunk(chunk=chunk, score=0.9, source="vector")
    assert scored.chunk.kind == "definition"


def test_question_file_parses() -> None:
    path = REPO_ROOT / "eval" / "questions.jsonl"
    assert load_questions(path) == []  # only placeholders so far
    assert len(load_questions(path, include_placeholders=True)) == 2
