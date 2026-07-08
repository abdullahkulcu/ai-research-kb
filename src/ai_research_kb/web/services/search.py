"""Lightweight keyword search over research docs.

Faz 2 will replace this with a real local embedding index (sentence-transformers +
sqlite-vec/chroma). The function signature/shape is kept stable on purpose so the
API and frontend don't need to change when that lands — only this module does.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ...repo import find_docs, parse_markdown

_SNIPPET_RADIUS = 80


def _snippet(body: str, query: str) -> str:
    if not query:
        return " ".join(body.strip().split())[: _SNIPPET_RADIUS * 2]
    idx = body.lower().find(query.lower())
    if idx == -1:
        return " ".join(body.strip().split())[: _SNIPPET_RADIUS * 2]
    start = max(0, idx - _SNIPPET_RADIUS)
    end = min(len(body), idx + len(query) + _SNIPPET_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(body) else ""
    return prefix + " ".join(body[start:end].strip().split()) + suffix


def search_docs(
    root: Path,
    query: str,
    cluster: str | None = None,
    status: str | None = None,
    doc_type: str | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in find_docs(root):
        if cluster and path.parent.name != cluster:
            continue
        try:
            doc = parse_markdown(path)
        except ValueError:
            continue

        fm = doc.frontmatter_raw
        if status and fm.get("status") != status:
            continue
        if doc_type and fm.get("doc_type") != doc_type:
            continue

        title = fm.get("title", path.stem)
        haystack = f"{title}\n{doc.body}"
        if query:
            score = len(re.findall(re.escape(query), haystack, re.IGNORECASE))
            if score == 0:
                continue
        else:
            score = 0

        results.append(
            {
                "cluster": path.parent.name,
                "doc": str(path.relative_to(root)),
                "title": title,
                "snippet": _snippet(doc.body, query),
                "score": score,
                "related_docs": fm.get("related_docs") or [],
            }
        )

    results.sort(key=lambda r: (-r["score"], r["title"]))
    return results
