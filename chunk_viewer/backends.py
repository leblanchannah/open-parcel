"""Chunking backends for the chunk viewer.

Each backend exposes:
  - ``PARAMS``: a list of ParamSpec describing its tunable knobs (the UI builds widgets from it)
  - ``run(pdf_path, first_page, last_page, params) -> list[ViewChunk]``

Page numbers are 1-based everywhere. Boxes are in PDF points with a TOP-LEFT origin
(the same space pymupdf uses), so the renderer can draw them directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .section_paths import fix_section_paths


@dataclass
class ViewChunk:
    id: str
    text: str
    boxes: list[tuple[int, float, float, float, float]]  # (page, x0, y0, x1, y1)
    kind: str = ""
    headings: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def pages(self) -> list[int]:
        return sorted({b[0] for b in self.boxes})


@dataclass
class ParamSpec:
    name: str
    default: Any
    group: str = "params"
    choices: tuple | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    help: str = ""


# --------------------------------------------------------------------------------------
# PyMuPDF4LLM layout chunker (what `pymupdf.Document.to_chunks` calls)
# --------------------------------------------------------------------------------------


def _pymupdf_params() -> list[ParamSpec]:
    """Built from the library's own DEFAULTS / WEIGHTS so new knobs show up automatically."""
    from pymupdf4llm.helpers.chunking import _ENUM_VALUES, DEFAULTS, WEIGHTS_LAYOUT

    specs: list[ParamSpec] = []
    skip = {"tokenizer", "weights"}
    for name, default in DEFAULTS.items():
        if name in skip:
            continue
        choices = _ENUM_VALUES.get(name)
        if isinstance(default, bool):
            specs.append(ParamSpec(name, default, "chunking"))
        elif isinstance(default, int):
            specs.append(ParamSpec(name, default, "chunking", min=0, max=8000, step=10))
        elif isinstance(default, float):
            specs.append(ParamSpec(name, default, "chunking", min=0.0, max=3.0, step=0.05))
        else:
            specs.append(ParamSpec(name, default, "chunking", choices=choices))

    specs.append(
        ParamSpec("table_output", "markdown", "parsing", choices=_ENUM_VALUES["table_output"])
    )
    specs.append(
        ParamSpec(
            "use_ocr",
            False,
            "parsing",
            help="Run OCR on pages that need it (slow; requires an OCR engine installed).",
        )
    )
    specs.append(
        ParamSpec(
            "edge_threshold",
            0.0,
            "parsing",
            min=0.0,
            max=50.0,
            step=0.5,
            help="0 = library default. Table edge threshold passed to parse_document.",
        )
    )
    specs.append(
        ParamSpec(
            "fix_section_paths",
            True,
            "post-processing",
            help="Rebuild heading paths from the bylaw's structure (Section > transect group > "
            "subheading) instead of font-size depth. The original path is kept in meta.",
        )
    )
    for name, default in WEIGHTS_LAYOUT.items():
        specs.append(
            ParamSpec(
                name,
                default,
                "boundary weights",
                min=0.0,
                max=2.0,
                step=0.05,
                help="Layout-signal weight in BoundaryScorer.",
            )
        )
    return specs


def run_pymupdf(pdf_path: str, first_page: int, last_page: int, params: dict) -> list[ViewChunk]:
    import pymupdf
    import pymupdf4llm
    from pymupdf4llm.helpers.chunking import WEIGHTS_LAYOUT

    params = dict(params)
    fix_paths = params.pop("fix_section_paths", False)
    weights = {k: params.pop(k) for k in list(params) if k in WEIGHTS_LAYOUT}
    if not params.pop("use_ocr", False):
        params["use_ocr"] = False
    else:
        params.pop("use_ocr", None)  # fall back to library default (auto OCR)
    if not params.get("edge_threshold"):
        params.pop("edge_threshold", None)

    doc = pymupdf.open(pdf_path)
    pages = list(range(first_page - 1, min(last_page, doc.page_count)))
    result = pymupdf4llm.to_chunks(doc, pages=pages, weights=weights, **params)

    out = []
    for c in result.chunks:
        m = c.metadata
        boxes = [(int(b[0]), *map(float, b[1:5])) for b in m.bboxes]
        out.append(
            ViewChunk(
                id=c.id,
                text=c.text,
                boxes=boxes,
                kind=", ".join(m.types),
                headings=list(m.section_path),
                meta={
                    "tokens": m.token_count,
                    "section_id": m.section_id,
                    "element_ids": list(m.element_ids),
                    "table_ids": list(m.table_ids),
                    "figure_ids": list(m.figure_ids),
                },
            )
        )
    if fix_paths:
        for c, fixed in zip(out, fix_section_paths([c.headings for c in out]), strict=True):
            if fixed != c.headings:
                c.meta["raw_section_path"] = " > ".join(c.headings)
            c.headings = fixed
    return out


# --------------------------------------------------------------------------------------
# Docling + HybridChunker
# --------------------------------------------------------------------------------------


def _docling_params() -> list[ParamSpec]:
    return [
        ParamSpec("do_ocr", False, "conversion"),
        ParamSpec("do_table_structure", True, "conversion"),
        ParamSpec("table_mode", "accurate", "conversion", choices=("accurate", "fast")),
        ParamSpec("do_cell_matching", True, "conversion"),
        ParamSpec(
            "tokenizer_model",
            "sentence-transformers/all-MiniLM-L6-v2",
            "chunking",
            help="HF tokenizer used by HybridChunker to measure chunk size.",
        ),
        ParamSpec("max_tokens", 512, "chunking", min=16, max=8192, step=16),
        ParamSpec("merge_peers", True, "chunking"),
        ParamSpec("repeat_table_header", True, "chunking"),
        ParamSpec("always_emit_headings", False, "chunking"),
    ]


def _docling_convert(pdf_path: str, first_page: int, last_page: int, conv: dict):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions(do_ocr=conv["do_ocr"], do_table_structure=conv["do_table_structure"])
    opts.table_structure_options.mode = TableFormerMode(conv["table_mode"])
    opts.table_structure_options.do_cell_matching = conv["do_cell_matching"]
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    return converter.convert(Path(pdf_path), page_range=(first_page, last_page)).document


def run_docling(pdf_path: str, first_page: int, last_page: int, params: dict) -> list[ViewChunk]:
    from docling.chunking import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from docling_core.types.doc import CoordOrigin

    conv_keys = ("do_ocr", "do_table_structure", "table_mode", "do_cell_matching")
    doc = _docling_convert_cached(
        pdf_path, first_page, last_page, {k: params[k] for k in conv_keys}
    )

    tokenizer = HuggingFaceTokenizer.from_pretrained(
        model_name=params["tokenizer_model"], max_tokens=int(params["max_tokens"])
    )
    chunker = HybridChunker(
        tokenizer=tokenizer,
        merge_peers=params["merge_peers"],
        repeat_table_header=params["repeat_table_header"],
        always_emit_headings=params["always_emit_headings"],
    )

    out = []
    for i, chunk in enumerate(chunker.chunk(dl_doc=doc)):
        boxes = []
        for item in chunk.meta.doc_items:
            for prov in item.prov:
                page_h = doc.pages[prov.page_no].size.height
                bb = prov.bbox
                if bb.coord_origin == CoordOrigin.BOTTOMLEFT:
                    bb = bb.to_top_left_origin(page_height=page_h)
                boxes.append((prov.page_no, bb.l, bb.t, bb.r, bb.b))
        out.append(
            ViewChunk(
                id=f"c{i}",
                text=chunk.text,
                boxes=boxes,
                kind=", ".join(sorted({str(it.label.value) for it in chunk.meta.doc_items})),
                headings=list(chunk.meta.headings or []),
                meta={
                    "tokens": tokenizer.count_tokens(chunker.contextualize(chunk)),
                    "contextualized": chunker.contextualize(chunk),
                },
            )
        )
    return out


# Docling conversion is the slow part; keep the last few conversions in memory so that
# tweaking chunker params does not reconvert.
_DOC_CACHE: dict = {}


def _docling_convert_cached(pdf_path, first_page, last_page, conv):
    key = (pdf_path, Path(pdf_path).stat().st_mtime, first_page, last_page, tuple(conv.items()))
    if key not in _DOC_CACHE:
        if len(_DOC_CACHE) > 4:
            _DOC_CACHE.pop(next(iter(_DOC_CACHE)))
        _DOC_CACHE[key] = _docling_convert(pdf_path, first_page, last_page, conv)
    return _DOC_CACHE[key]


BACKENDS = {
    "pymupdf4llm (to_chunks)": (_pymupdf_params, run_pymupdf),
    "docling (HybridChunker)": (_docling_params, run_docling),
}
