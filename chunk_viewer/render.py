"""Builds self-contained HTML viewers for chunker output.

``build_html``: one run. PDF pages with chunk boxes (left) and the chunk list (right).
``build_compare_html``: two runs side by side. Each column has the PDF with that run's boxes on
top and its chunk list underneath, and the two PDF panes scroll together.

In both views: scrolling a PDF pane auto-scrolls its chunk list to the chunks on the visible
page, hovering a chunk card highlights its boxes, clicking a card jumps to it on the PDF, and
clicking a box jumps to its card.
"""

from __future__ import annotations

import base64
import colorsys
import html
import json

import pymupdf

from .backends import ViewChunk


def _color(i: int) -> str:
    h = (i * 0.618033988749895) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, 0.45, 0.75)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def render_pages(pdf_path: str, first_page: int, last_page: int, dpi: int) -> list[dict]:
    doc = pymupdf.open(pdf_path)
    pages = []
    for pno in range(first_page, min(last_page, doc.page_count) + 1):
        page = doc[pno - 1]
        png = page.get_pixmap(dpi=dpi).tobytes("png")
        pages.append(
            {
                "page": pno,
                "w": page.rect.width,
                "h": page.rect.height,
                "src": "data:image/png;base64," + base64.b64encode(png).decode(),
            }
        )
    return pages


def _pages_html(pages: list[dict], chunks: list[ViewChunk]) -> str:
    out = []
    for p in pages:
        rects = []
        for ci, c in enumerate(chunks):
            col = _color(ci)
            for bi, (pg, x0, y0, x1, y1) in enumerate(c.boxes):
                if pg != p["page"]:
                    continue
                label = (
                    f'<text x="{x0 + 1:.1f}" y="{y0 - 1.5:.1f}" fill="{col}">'
                    f"{html.escape(c.id)}</text>"
                    if bi == 0 or c.boxes[bi - 1][0] != pg
                    else ""
                )
                rects.append(
                    f'<g class="box" data-c="{ci}"><rect x="{x0:.1f}" y="{y0:.1f}" '
                    f'width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" stroke="{col}" '
                    f'fill="{col}"/>{label}</g>'
                )
        out.append(
            f'<div class="page" data-page="{p["page"]}"><div class="pno">page {p["page"]}</div>'
            f'<div class="pwrap"><img src="{p["src"]}"/>'
            f'<svg viewBox="0 0 {p["w"]:.1f} {p["h"]:.1f}" preserveAspectRatio="none">'
            f"{''.join(rects)}</svg></div></div>"
        )
    return "".join(out)


def _cards_html(chunks: list[ViewChunk], page_nums: set[int]) -> str:
    cards = []
    for ci, c in enumerate(chunks):
        pages_str = ", ".join(str(x) for x in c.pages) or "—"
        meta = {
            k: v for k, v in c.meta.items() if v not in (None, [], "") and k != "contextualized"
        }
        ctx = c.meta.get("contextualized")
        offpage = [x for x in c.pages if x not in page_nums]
        cards.append(
            f'<div class="card" data-c="{ci}" style="border-left-color:{_color(ci)}">'
            f'<div class="hdr"><b>{html.escape(c.id)}</b> · p.{pages_str}'
            f' · <span class="kind">{html.escape(c.kind)}</span>'
            + (f' <span class="warn">spills to p.{offpage}</span>' if offpage else "")
            + "</div>"
            + (
                f'<div class="path">{html.escape(" › ".join(c.headings))}</div>'
                if c.headings
                else ""
            )
            + f'<pre class="txt">{html.escape(c.text)}</pre>'
            + (
                f"<details><summary>contextualized</summary><pre>{html.escape(ctx)}</pre></details>"
                if ctx
                else ""
            )
            + f'<div class="meta">{html.escape(json.dumps(meta, default=str))}</div></div>'
        )
    return "".join(cards)


_CSS = """
:root { color-scheme: light; }
body { margin:0; font-family: system-ui, sans-serif; background:#f3f3f3; }
.pdf, .list { overflow-y:auto; }
.pdf { padding:6px; }
.list { padding:6px; }
.page { margin-bottom:14px; }
.pno { font-size:12px; color:#666; margin:2px 0; }
.pwrap { position:relative; box-shadow:0 1px 4px #0003; background:#fff; }
.pwrap img { width:100%; display:block; }
.pwrap svg { position:absolute; inset:0; width:100%; height:100%; }
.box rect { fill-opacity:0.08; stroke-width:0.8; cursor:pointer; }
.box text { font-size:7px; font-weight:700; pointer-events:none; }
.box.hl rect { fill-opacity:0.35; stroke-width:2; }
.card { background:#fff; border-left:6px solid; border-radius:4px; padding:6px 8px;
        margin-bottom:8px; font-size:12px; cursor:pointer; box-shadow:0 1px 2px #0002; }
.card.hl { outline:2px solid #333; }
.hdr { margin-bottom:3px; }
.kind { color:#555; }
.warn { color:#b45309; }
.path { color:#2563eb; font-size:11px; margin-bottom:3px; }
pre { white-space:pre-wrap; word-break:break-word; margin:4px 0; font-size:11.5px;
      font-family: ui-monospace, monospace; max-height:320px; overflow:auto; }
.meta { color:#888; font-size:10px; font-family:ui-monospace, monospace; }
#bar { font-size:12px; padding:4px 6px; }
.title { font-size:13px; font-weight:700; padding:4px 6px; background:#e5e7eb; }
"""

# Wires up one .pane (a .pdf and a .list). Highlights are scoped to the pane, so the same chunk
# index in the other pane is not touched. With "sync PDF panes" on, scrolling one PDF pane
# scrolls the others to the same relative position (they render the same pages at the same
# width, so this lines pages up).
_JS = """
const syncList = document.getElementById('sync');
const syncPdf = document.getElementById('syncpdf');
const panes = [...document.querySelectorAll('.pane')];
let mirroring = false;
panes.forEach(pane => {
  const pdf = pane.querySelector('.pdf'), list = pane.querySelector('.list');
  let suppress = false, lastPage = null;
  const hl = (c, on) => pane.querySelectorAll('[data-c="'+c+'"]')
                            .forEach(e => e.classList.toggle('hl', on));
  pane.querySelectorAll('.card').forEach(card => {
    const c = card.dataset.c;
    card.addEventListener('mouseenter', () => hl(c, true));
    card.addEventListener('mouseleave', () => hl(c, false));
    card.addEventListener('click', () => {
      const box = pdf.querySelector('.box[data-c="'+c+'"]');
      if (!box) return;
      suppress = true;
      pdf.scrollTop += box.getBoundingClientRect().top - pdf.getBoundingClientRect().top - 60;
      setTimeout(() => suppress = false, 400);
    });
  });
  pane.querySelectorAll('.box').forEach(box => {
    const c = box.dataset.c;
    box.addEventListener('mouseenter', () => hl(c, true));
    box.addEventListener('mouseleave', () => hl(c, false));
    box.addEventListener('click', () => {
      const card = list.querySelector('.card[data-c="'+c+'"]');
      list.scrollTop += card.getBoundingClientRect().top - list.getBoundingClientRect().top - 10;
    });
  });
  pdf.addEventListener('scroll', () => {
    if (syncPdf && syncPdf.checked && !mirroring) {
      mirroring = true;
      const ratio = pdf.scrollTop / Math.max(1, pdf.scrollHeight - pdf.clientHeight);
      panes.forEach(o => {
        if (o === pane) return;
        const op = o.querySelector('.pdf');
        op.scrollTop = ratio * (op.scrollHeight - op.clientHeight);
      });
      requestAnimationFrame(() => mirroring = false);
    }
    if (!syncList.checked || suppress) return;
    const top = pdf.getBoundingClientRect().top + pdf.clientHeight * 0.3;
    let cur = null;
    for (const p of pdf.querySelectorAll('.page')) {
      if (p.getBoundingClientRect().top <= top) cur = p.dataset.page; else break;
    }
    if (cur === null || cur === lastPage) return;
    lastPage = cur;
    const box = pdf.querySelector('.page[data-page="'+cur+'"] .box');
    if (!box) return;
    const card = list.querySelector('.card[data-c="'+box.dataset.c+'"]');
    list.scrollTo({top: list.scrollTop + card.getBoundingClientRect().top
                   - list.getBoundingClientRect().top - 6, behavior: 'smooth'});
  });
});
"""


def _doc(css: str, body: str) -> str:
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><style>{_CSS}{css}</style></head>'
        f"<body>{body}<script>{_JS}</script></body></html>"
    )


def build_html(pages: list[dict], chunks: list[ViewChunk], height: int = 900) -> str:
    page_nums = {p["page"] for p in pages}
    css = f"""
.pane {{ display:flex; gap:8px; height:{height}px; }}
.pane .pdf {{ flex:1.3; }} .pane .list {{ flex:1; }}
"""
    body = (
        f'<div id="bar">{len(chunks)} chunks · {len(pages)} pages · '
        '<label><input type="checkbox" id="sync" checked> sync chunk list to PDF scroll</label>'
        "</div>"
        f'<div class="pane"><div class="pdf">{_pages_html(pages, chunks)}</div>'
        f'<div class="list">{_cards_html(chunks, page_nums)}</div></div>'
    )
    return _doc(css, body)


def build_compare_html(
    pages: list[dict], runs: list[tuple[str, list[ViewChunk]]], height: int = 900
) -> str:
    """Side-by-side view of several runs over the same pages (normally two)."""
    page_nums = {p["page"] for p in pages}
    pdf_h = int(height * 0.62)
    css = f"""
#cols {{ display:flex; gap:10px; }}
.pane {{ flex:1; min-width:0; display:flex; flex-direction:column; background:#fafafa; }}
.pane .pdf {{ height:{pdf_h}px; }}
.pane .list {{ height:{height - pdf_h - 30}px; border-top:2px solid #d1d5db; }}
"""
    cols = "".join(
        f'<div class="pane"><div class="title">{html.escape(label)} · {len(chunks)} chunks</div>'
        f'<div class="pdf">{_pages_html(pages, chunks)}</div>'
        f'<div class="list">{_cards_html(chunks, page_nums)}</div></div>'
        for label, chunks in runs
    )
    body = (
        f'<div id="bar">{len(pages)} pages · '
        '<label><input type="checkbox" id="syncpdf" checked> scroll PDF panes together</label> · '
        '<label><input type="checkbox" id="sync" checked> sync chunk lists to PDF scroll</label>'
        f'</div><div id="cols">{cols}</div>'
    )
    return _doc(css, body)
