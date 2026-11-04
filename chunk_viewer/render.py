"""Builds a self-contained HTML viewer: PDF pages with chunk boxes (left) + chunk list (right).

Scrolling the PDF pane auto-scrolls the chunk list to the chunks on the visible page.
Hover a chunk card to highlight its boxes; click a card to jump to it on the PDF;
click a box to jump to its card.
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


def build_html(pages: list[dict], chunks: list[ViewChunk], height: int = 900) -> str:
    page_nums = {p["page"] for p in pages}
    page_html = []
    for p in pages:
        rects = []
        for ci, c in enumerate(chunks):
            col = _color(ci)
            for bi, (pg, x0, y0, x1, y1) in enumerate(c.boxes):
                if pg != p["page"]:
                    continue
                label = (
                    f'<text x="{x0 + 1:.1f}" y="{y0 - 1.5:.1f}" fill="{col}">{c.id}</text>'
                    if bi == 0 or c.boxes[bi - 1][0] != pg
                    else ""
                )
                rects.append(
                    f'<g class="box" data-c="{ci}"><rect x="{x0:.1f}" y="{y0:.1f}" '
                    f'width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" stroke="{col}" '
                    f'fill="{col}"/>{label}</g>'
                )
        page_html.append(
            f'<div class="page" data-page="{p["page"]}"><div class="pno">page {p["page"]}</div>'
            f'<div class="pwrap"><img src="{p["src"]}"/>'
            f'<svg viewBox="0 0 {p["w"]:.1f} {p["h"]:.1f}" preserveAspectRatio="none">'
            f"{''.join(rects)}</svg></div></div>"
        )

    cards = []
    for ci, c in enumerate(chunks):
        pages_str = ", ".join(str(x) for x in c.pages) or "—"
        meta = {
            k: v for k, v in c.meta.items() if v not in (None, [], "") and k != "contextualized"
        }
        ctx = c.meta.get("contextualized")
        offpage = [x for x in c.pages if x not in page_nums]
        cards.append(
            f'<div class="card" id="card{ci}" data-c="{ci}" data-first-page="'
            f'{c.pages[0] if c.pages else -1}" style="border-left-color:{_color(ci)}">'
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

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ color-scheme: light; }}
body {{ margin:0; font-family: system-ui, sans-serif; background:#f3f3f3; }}
#wrap {{ display:flex; gap:8px; height:{height}px; }}
#pdf, #list {{ overflow-y:auto; height:100%; }}
#pdf {{ flex: 1.3; padding:6px; }}
#list {{ flex: 1; padding:6px; }}
.page {{ margin-bottom:14px; }}
.pno {{ font-size:12px; color:#666; margin:2px 0; }}
.pwrap {{ position:relative; box-shadow:0 1px 4px #0003; background:#fff; }}
.pwrap img {{ width:100%; display:block; }}
.pwrap svg {{ position:absolute; inset:0; width:100%; height:100%; }}
.box rect {{ fill-opacity:0.08; stroke-width:0.8; cursor:pointer; }}
.box text {{ font-size:7px; font-weight:700; pointer-events:none; }}
.box.hl rect {{ fill-opacity:0.35; stroke-width:2; }}
.card {{ background:#fff; border-left:6px solid; border-radius:4px; padding:6px 8px;
        margin-bottom:8px; font-size:12px; cursor:pointer; box-shadow:0 1px 2px #0002; }}
.card.hl {{ outline:2px solid #333; }}
.hdr {{ margin-bottom:3px; }}
.kind {{ color:#555; }}
.warn {{ color:#b45309; }}
.path {{ color:#2563eb; font-size:11px; margin-bottom:3px; }}
pre {{ white-space:pre-wrap; word-break:break-word; margin:4px 0; font-size:11.5px;
       font-family: ui-monospace, monospace; max-height:320px; overflow:auto; }}
.meta {{ color:#888; font-size:10px; font-family:ui-monospace, monospace; }}
#bar {{ font-size:12px; padding:4px 6px; }}
</style></head><body>
<div id="bar">{len(chunks)} chunks · {len(pages)} pages ·
<label><input type="checkbox" id="sync" checked> sync chunk list to PDF scroll</label></div>
<div id="wrap"><div id="pdf">{"".join(page_html)}</div><div id="list">{"".join(cards)}</div></div>
<script>
const pdf = document.getElementById('pdf'), list = document.getElementById('list');
const sync = document.getElementById('sync');
let suppress = false;
function hl(c, on) {{
  document.querySelectorAll('[data-c="'+c+'"]').forEach(e => e.classList.toggle('hl', on));
}}
document.querySelectorAll('.card').forEach(card => {{
  const c = card.dataset.c;
  card.addEventListener('mouseenter', () => hl(c, true));
  card.addEventListener('mouseleave', () => hl(c, false));
  card.addEventListener('click', () => {{
    const box = pdf.querySelector('.box[data-c="'+c+'"]');
    if (!box) return;
    suppress = true;
    const r = box.getBoundingClientRect(), pr = pdf.getBoundingClientRect();
    pdf.scrollTop += r.top - pr.top - 60;
    setTimeout(() => suppress = false, 400);
  }});
}});
document.querySelectorAll('.box').forEach(box => {{
  const c = box.dataset.c;
  box.addEventListener('mouseenter', () => hl(c, true));
  box.addEventListener('mouseleave', () => hl(c, false));
  box.addEventListener('click', () => {{
    const card = document.getElementById('card'+c);
    list.scrollTop += card.getBoundingClientRect().top - list.getBoundingClientRect().top - 10;
  }});
}});
let lastPage = null;
pdf.addEventListener('scroll', () => {{
  if (!sync.checked || suppress) return;
  const top = pdf.getBoundingClientRect().top + pdf.clientHeight * 0.3;
  let cur = null;
  for (const p of pdf.querySelectorAll('.page')) {{
    if (p.getBoundingClientRect().top <= top) cur = p.dataset.page; else break;
  }}
  if (cur === null || cur === lastPage) return;
  lastPage = cur;
  // first chunk that has a box on this page
  const box = pdf.querySelector('.page[data-page="'+cur+'"] .box');
  if (!box) return;
  const card = document.getElementById('card'+box.dataset.c);
  list.scrollTo({{top: list.scrollTop + card.getBoundingClientRect().top
                 - list.getBoundingClientRect().top - 6, behavior: 'smooth'}});
}});
</script></body></html>"""
