"""Streamlit chunk inspector.

uv run streamlit run chunk_viewer/app.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import pymupdf
import streamlit as st
import streamlit.components.v1 as components

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from chunk_viewer.backends import BACKENDS, ParamSpec  # noqa: E402
from chunk_viewer.render import build_html, render_pages  # noqa: E402

DEFAULT_PDF = REPO / "data/ottawa/2026-050.pdf"
OUTPUT_DIR = REPO / "data/ottawa/output"

st.set_page_config(page_title="Chunk viewer", layout="wide")


@st.cache_data(show_spinner=False, max_entries=20)
def run_backend(backend: str, pdf_path: str, mtime: float, first: int, last: int, params_json: str):
    _, run = BACKENDS[backend]
    t0 = time.perf_counter()
    chunks = run(pdf_path, first, last, json.loads(params_json))
    return chunks, time.perf_counter() - t0


@st.cache_data(show_spinner=False, max_entries=20)
def cached_pages(pdf_path: str, mtime: float, first: int, last: int, dpi: int):
    return render_pages(pdf_path, first, last, dpi)


def widget(spec: ParamSpec, key: str):
    label, d = spec.name, spec.default
    kw = {"help": spec.help or None, "key": key}
    if spec.choices:
        return st.selectbox(label, spec.choices, index=list(spec.choices).index(d), **kw)
    if isinstance(d, bool):
        return st.checkbox(label, value=d, **kw)
    if isinstance(d, int):
        return int(
            st.number_input(
                label, value=d, min_value=int(spec.min or 0), step=int(spec.step or 1), **kw
            )
        )
    if isinstance(d, float):
        return float(
            st.number_input(
                label,
                value=d,
                min_value=spec.min,
                max_value=spec.max,
                step=spec.step or 0.05,
                format="%.3f",
                **kw,
            )
        )
    return st.text_input(label, value=str(d), **kw)


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Document")
    upload = st.file_uploader("Upload a PDF", type="pdf")
    if upload is not None:
        tmp = Path(tempfile.gettempdir()) / f"chunk_viewer_{upload.name}"
        tmp.write_bytes(upload.getvalue())
        pdf_path = str(tmp)
    else:
        pdf_path = st.text_input("…or PDF path", value=str(DEFAULT_PDF))

    if not Path(pdf_path).exists():
        st.error(f"Not found: {pdf_path}")
        st.stop()
    mtime = Path(pdf_path).stat().st_mtime
    n_pages = pymupdf.open(pdf_path).page_count
    st.caption(f"{n_pages} pages")

    backend = st.selectbox("Chunker", list(BACKENDS))
    param_fn, _ = BACKENDS[backend]
    specs = param_fn()

    with st.form("run"):
        c1, c2 = st.columns(2)
        first = int(c1.number_input("first page", 1, n_pages, value=min(14, n_pages)))
        last = int(c2.number_input("last page", 1, n_pages, value=min(18, n_pages)))
        params = {}
        groups = list(dict.fromkeys(s.group for s in specs))
        for g in groups:
            with st.expander(g, expanded=(g == groups[0])):
                for s in (s for s in specs if s.group == g):
                    params[s.name] = widget(s, key=f"{backend}:{s.name}")
        submitted = st.form_submit_button("Run chunker", type="primary")

    st.header("Display")
    dpi = st.slider("page render dpi", 50, 200, 100, 10)
    height = st.slider("viewer height (px)", 400, 1600, 950, 50)
    kind_filter = st.text_input("only chunks whose type contains", "")

if last < first:
    st.error("last page must be ≥ first page")
    st.stop()

run_key = (backend, pdf_path, first, last, json.dumps(params, sort_keys=True))
if submitted:
    st.session_state["run_key"] = run_key
if "run_key" not in st.session_state:
    st.info("Pick a page range and params in the sidebar, then **Run chunker**.")
    st.stop()

backend, pdf_path, first, last, params_json = st.session_state["run_key"]
if st.session_state["run_key"] != run_key:
    st.caption("⚠️ Sidebar params changed since the last run, press **Run chunker** to apply.")

with st.spinner(f"Running {backend} on pages {first}–{last}…"):
    try:
        chunks, secs = run_backend(backend, pdf_path, mtime, first, last, params_json)
    except Exception as e:  # surface library errors (bad params etc.) in the UI
        st.exception(e)
        st.stop()
    pages = cached_pages(pdf_path, mtime, first, last, dpi)

shown = [c for c in chunks if kind_filter.lower() in c.kind.lower()] if kind_filter else chunks

tokens = [c.meta.get("tokens") or 0 for c in chunks]
m1, m2, m3, m4 = st.columns(4)
m1.metric("chunks", len(chunks))
m2.metric("median tokens", int(pd.Series(tokens).median()) if tokens else 0)
m3.metric("max tokens", max(tokens, default=0))
m4.metric("runtime", f"{secs:.1f}s")

components.html(build_html(pages, shown, height=height), height=height + 40, scrolling=False)

with st.expander("Chunks table / export"):
    df = pd.DataFrame(
        [
            {
                "id": c.id,
                "pages": c.pages,
                "kind": c.kind,
                "path": " > ".join(c.headings),
                "tokens": c.meta.get("tokens"),
                "n_chars": len(c.text),
                "text": c.text,
            }
            for c in chunks
        ]
    )
    st.dataframe(df, width="stretch", height=300)
    st.code(f"# params used\n{backend}\n{json.dumps(json.loads(params_json), indent=2)}", "json")
    if st.button("Save to data/ottawa/output/viewer_chunks.parquet"):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out = pd.DataFrame([asdict(c) for c in chunks])
        out["meta"] = out["meta"].map(lambda m: json.dumps(m, default=str))
        out.to_parquet(OUTPUT_DIR / "viewer_chunks.parquet")
        st.success("saved")
