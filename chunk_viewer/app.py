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
from chunk_viewer.render import build_compare_html, build_html, render_pages  # noqa: E402

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


def chunker_controls(slot: str, default_index: int) -> tuple[str, list[ParamSpec]]:
    """Chunker picker. Lives outside the form so changing it swaps the param widgets."""
    name = st.selectbox(f"Chunker {slot}", list(BACKENDS), index=default_index, key=f"be{slot}")
    return name, BACKENDS[name][0]()


def param_widgets(slot: str, backend: str, specs: list[ParamSpec]) -> dict:
    params = {}
    groups = list(dict.fromkeys(s.group for s in specs))
    for g in groups:
        with st.expander(f"{slot} · {g}", expanded=False):
            for s in (s for s in specs if s.group == g):
                params[s.name] = widget(s, key=f"{slot}:{backend}:{s.name}")
    return params


def run_stats(label: str, chunks: list, secs: float) -> dict:
    tokens = pd.Series([c.meta.get("tokens") or 0 for c in chunks], dtype="float")
    kinds = pd.Series([k for c in chunks for k in c.kind.split(", ") if k]).value_counts()
    return {
        "chunker": label,
        "chunks": len(chunks),
        "median tokens": int(tokens.median()) if len(tokens) else 0,
        "max tokens": int(tokens.max()) if len(tokens) else 0,
        "multi-page chunks": sum(len(c.pages) > 1 for c in chunks),
        "chunks with no boxes": sum(not c.boxes for c in chunks),
        "runtime (s)": round(secs, 1),
        "kinds": ", ".join(f"{k} {v}" for k, v in kinds.items()),
    }


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

    compare = st.toggle("Compare two chunkers side by side", value=True)
    slots = ["A", "B"] if compare else ["A"]
    picked = {slot: chunker_controls(slot, i % len(BACKENDS)) for i, slot in enumerate(slots)}

    with st.form("run"):
        c1, c2 = st.columns(2)
        first = int(c1.number_input("first page", 1, n_pages, value=min(14, n_pages)))
        last = int(c2.number_input("last page", 1, n_pages, value=min(18, n_pages)))
        params = {
            slot: param_widgets(slot, backend, specs) for slot, (backend, specs) in picked.items()
        }
        submitted = st.form_submit_button("Run", type="primary")

    st.header("Display")
    dpi = st.slider("page render dpi", 50, 200, 100, 10)
    height = st.slider("viewer height (px)", 400, 1600, 950, 50)
    kind_filter = st.text_input("only chunks whose type contains", "")

if last < first:
    st.error("last page must be ≥ first page")
    st.stop()

runs_spec = tuple(
    (slot, backend, json.dumps(params[slot], sort_keys=True))
    for slot, (backend, _) in picked.items()
)
run_key = (pdf_path, first, last, runs_spec)
if submitted:
    st.session_state["run_key"] = run_key
if "run_key" not in st.session_state:
    st.info("Pick a page range, chunker(s) and params in the sidebar, then press **Run**.")
    st.stop()

if st.session_state["run_key"] != run_key:
    st.caption("⚠️ Sidebar settings changed since the last run, press **Run** to apply.")
pdf_path, first, last, runs_spec = st.session_state["run_key"]
mtime = Path(pdf_path).stat().st_mtime

results = []  # (label, backend, params_json, chunks, secs)
for slot, backend, params_json in runs_spec:
    label = f"{slot}: {backend}"
    with st.spinner(f"Running {backend} on pages {first}–{last}…"):
        try:
            chunks, secs = run_backend(backend, pdf_path, mtime, first, last, params_json)
        except Exception as e:  # surface library errors (bad params, model downloads) in the UI
            st.error(f"{label} failed: {type(e).__name__}: {e}")
            with st.expander("traceback"):
                st.exception(e)
            continue
    results.append((label, backend, params_json, chunks, secs))
if not results:
    st.stop()
pages = cached_pages(pdf_path, mtime, first, last, dpi)


def keep(c) -> bool:
    return kind_filter.lower() in c.kind.lower()


st.dataframe(
    pd.DataFrame([run_stats(lbl, ch, secs) for lbl, _, _, ch, secs in results]),
    hide_index=True,
    width="stretch",
)

if len(results) == 1:
    _, _, _, chunks, _ = results[0]
    shown = [c for c in chunks if keep(c)]
    components.html(build_html(pages, shown, height=height), height=height + 40, scrolling=False)
else:
    runs = [(lbl, [c for c in ch if keep(c)]) for lbl, _, _, ch, _ in results]
    components.html(
        build_compare_html(pages, runs, height=height), height=height + 70, scrolling=False
    )

with st.expander("Chunks table / export"):
    tabs = st.tabs([lbl for lbl, *_ in results])
    for tab, (label, backend, params_json, chunks, _) in zip(tabs, results, strict=True):
        with tab:
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
            st.code(
                f"# params used\n{backend}\n{json.dumps(json.loads(params_json), indent=2)}",
                "json",
            )
            slug = label.split(":")[0].lower()
            fname = f"viewer_chunks_{slug}.parquet"
            if st.button(f"Save to data/ottawa/output/{fname}", key=f"save_{slug}"):
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                out = pd.DataFrame([asdict(c) for c in chunks])
                out["meta"] = out["meta"].map(lambda m: json.dumps(m, default=str))
                out["chunker"] = backend
                out["params"] = params_json
                out.to_parquet(OUTPUT_DIR / fname)
                st.success("saved")
