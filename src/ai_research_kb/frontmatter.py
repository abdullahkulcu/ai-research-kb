"""Frontmatter schema validation.

This is the "critical" gate: schema violations and cluster/folder mismatches are
errors that should fail CI. Cross-reference existence and other soft signals live
in consistency.py and are reported, not enforced.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from .models import Frontmatter
from .repo import ParsedDoc, find_docs, parse_markdown

Severity = Literal["error", "warning"]


@dataclass
class Issue:
    path: Path
    severity: Severity
    code: str
    message: str


def validate_doc(doc: ParsedDoc) -> tuple[Frontmatter | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        fm = Frontmatter.model_validate(doc.frontmatter_raw)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            issues.append(Issue(doc.path, "error", "frontmatter-schema", f"{loc}: {err['msg']}"))
        return None, issues

    expected_cluster = doc.path.parent.name
    if fm.cluster != expected_cluster:
        issues.append(
            Issue(
                doc.path,
                "error",
                "cluster-mismatch",
                f"frontmatter cluster='{fm.cluster}' ancak klasör='{expected_cluster}'",
            )
        )

    if fm.updated < fm.created:
        issues.append(Issue(doc.path, "warning", "date-order", "updated, created'dan önce"))

    return fm, issues


def validate_tree(root: Path) -> dict[Path, tuple[Frontmatter | None, list[Issue]]]:
    results: dict[Path, tuple[Frontmatter | None, list[Issue]]] = {}
    for path in find_docs(root):
        try:
            doc = parse_markdown(path)
        except ValueError as e:
            results[path] = (None, [Issue(path, "error", "parse-error", str(e))])
            continue
        results[path] = validate_doc(doc)
    return results
