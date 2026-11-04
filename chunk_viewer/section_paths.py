"""Rebuild chunk section paths from the bylaw's own heading structure.

pymupdf4llm gives each heading a depth from its font-size rank alone. The bylaw is not
typeset consistently: in s.202 "Urban Transects" is 18pt but "Rural Transect" is 16pt, the
same size as the subheadings under it. So "Rural Transect" becomes a sibling of its own
subheadings, and every rural provision after it inherits "Urban Transects" as its parent.

This module ignores font depth and assigns levels by what the heading says:

1. ``Section NNN – Title`` (and ``Part N``) start a new top-level section.
2. Group headings such as ``Urban Transects`` / ``Rural Transect`` sit under the section.
3. Every other heading sits under the current group if there is one, else under the section.

It works on the sequence of section paths that the chunker produced (one per chunk, in
document order), so it does not need the PDF.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

SECTION_RE = re.compile(r"^(Section\s+\d+[A-Za-z]?\b|Part\s+\d+\b)", re.IGNORECASE)
GROUP_RE = re.compile(r"^[A-Z][\w\- ]*\bTransects?$")


def clean_heading(text: str) -> str:
    """Drop markdown emphasis and stray whitespace (e.g. ``Additional Dwelling Unit**``)."""
    return re.sub(r"\s+", " ", text.replace("**", "").replace("__", "")).strip(" #")


def heading_level(text: str) -> int:
    if SECTION_RE.match(text):
        return 1
    if GROUP_RE.match(text):
        return 2
    return 3


def fix_section_paths(paths: Sequence[Sequence[str]]) -> list[list[str]]:
    """Return corrected section paths, one per input path, in the same order.

    A chunk's nearest heading is the last element of its path. Whenever that changes from
    the previous chunk, the heading is placed in the stack by ``heading_level``.
    """
    stack: dict[int, str] = {}
    prev_last: str | None = None
    out: list[list[str]] = []
    for path in paths:
        cleaned = [clean_heading(h) for h in path if clean_heading(h)]
        if not cleaned:
            out.append([stack[k] for k in sorted(stack)])
            continue
        last = cleaned[-1]
        if last != prev_last:
            # Make sure the top-level section is known even if a chunk skipped its heading.
            top = next((h for h in cleaned if heading_level(h) == 1), None)
            if top is not None and stack.get(1) != top:
                stack = {1: top}
            lvl = heading_level(last)
            stack = {k: v for k, v in stack.items() if k < lvl}
            stack[lvl] = last
            prev_last = last
        out.append([stack[k] for k in sorted(stack)])
    return out
