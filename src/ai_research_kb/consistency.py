"""Consistency & optimization report (Faz 1, item 3): a-e checks over a cluster or repo.

Everything here is a *report*, not a gate — CI surfaces it as a PR comment but does
not fail the build on it (frontmatter.py / comments.py cover the blocking checks).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import load_config
from .llm import get_llm_provider
from .repo import find_docs, find_repo_root, parse_markdown

INLINE_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md[^)]*)\)")


@dataclass
class ConsistencyFinding:
    category: str
    severity: str  # "info" | "warning"
    cluster: str
    doc: str
    message: str


@dataclass
class ConsistencyReport:
    findings: list[ConsistencyFinding] = field(default_factory=list)
    llm_skipped: bool = False

    def by_category(self) -> dict[str, list[ConsistencyFinding]]:
        out: dict[str, list[ConsistencyFinding]] = {}
        for f in self.findings:
            out.setdefault(f.category, []).append(f)
        return out


def _docs_for(root: Path, cluster: str | None) -> list[Path]:
    docs = find_docs(root)
    if cluster:
        docs = [d for d in docs if d.parent.name == cluster]
    return docs


def check_broken_cross_references(root: Path, docs: list[Path]) -> list[ConsistencyFinding]:
    """3a: related_docs frontmatter entries and inline markdown links that don't resolve."""
    findings = []
    known = {d.resolve() for d in find_docs(root)}
    for path in docs:
        try:
            doc = parse_markdown(path)
        except ValueError:
            continue

        for rel in doc.frontmatter_raw.get("related_docs") or []:
            target = (path.parent / rel).resolve()
            if target not in known:
                findings.append(
                    ConsistencyFinding(
                        "broken-cross-reference",
                        "warning",
                        path.parent.name,
                        str(path),
                        f"related_docs kırık: {rel}",
                    )
                )

        for m in INLINE_LINK_RE.finditer(doc.body):
            link = m.group(1).split("#")[0]
            if link.startswith("http://") or link.startswith("https://"):
                continue
            target = (path.parent / link).resolve()
            if target not in known:
                findings.append(
                    ConsistencyFinding(
                        "broken-cross-reference",
                        "warning",
                        path.parent.name,
                        str(path),
                        f"kırık iç link: {link}",
                    )
                )
    return findings


def check_terminology(
    root: Path, docs: list[Path], canonical_terms: list[dict]
) -> list[ConsistencyFinding]:
    """3b: usages of a configured alias instead of its canonical term."""
    findings = []
    if not canonical_terms:
        return findings
    for path in docs:
        try:
            doc = parse_markdown(path)
        except ValueError:
            continue
        for entry in canonical_terms:
            canonical = entry.get("term")
            if not canonical:
                continue
            for alias in entry.get("aliases", []):
                if alias.lower() == canonical.lower():
                    continue
                if re.search(rf"\b{re.escape(alias)}\b", doc.body, re.IGNORECASE):
                    findings.append(
                        ConsistencyFinding(
                            "terminology",
                            "info",
                            path.parent.name,
                            str(path),
                            f"'{alias}' kullanılmış, kanonik terim '{canonical}' önerilir",
                        )
                    )
    return findings


def check_time_sensitive(
    root: Path, docs: list[Path], patterns: list[str]
) -> list[ConsistencyFinding]:
    """3d: date/beta/GA-style claims likely to go stale."""
    findings = []
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    for path in docs:
        try:
            doc = parse_markdown(path)
        except ValueError:
            continue
        for line_no, line in enumerate(doc.body.splitlines(), start=1):
            for pat in compiled:
                if pat.search(line):
                    findings.append(
                        ConsistencyFinding(
                            "time-sensitive",
                            "info",
                            path.parent.name,
                            str(path),
                            f"satır {line_no}: {line.strip()[:160]}",
                        )
                    )
                    break
    return findings


def check_structure_gaps(
    root: Path, docs: list[Path], expected_sections: dict[str, list[str]]
) -> list[ConsistencyFinding]:
    """3e: missing sections configured as expected for a doc_type."""
    findings = []
    for path in docs:
        try:
            doc = parse_markdown(path)
        except ValueError:
            continue
        doc_type = doc.frontmatter_raw.get("doc_type")
        expected = expected_sections.get(doc_type, [])
        if not expected:
            continue
        headings = {h.lower() for h in doc.headings()}
        for section in expected:
            if section.lower() not in headings:
                findings.append(
                    ConsistencyFinding(
                        "structure-gap",
                        "info",
                        path.parent.name,
                        str(path),
                        f"beklenen bölüm eksik: '{section}'",
                    )
                )
    return findings


def check_contradictions(
    cluster_docs: dict[str, list[Path]], config_root: Path | None = None
) -> tuple[list[ConsistencyFinding], bool]:
    """3c: LLM-optional contradiction candidates. Returns (findings, skipped)."""
    provider = get_llm_provider(config_root)
    if provider is None:
        return [], True
    findings = []
    for cluster, paths in cluster_docs.items():
        if len(paths) < 2:
            continue
        for candidate in provider.find_contradictions(cluster, paths):
            findings.append(
                ConsistencyFinding(
                    "contradiction-candidate",
                    "warning",
                    cluster,
                    candidate.get("doc", cluster),
                    candidate.get("message", ""),
                )
            )
    return findings, False


def run_consistency_check(root: Path, cluster: str | None = None) -> ConsistencyReport:
    # config.yaml lives at the repo root, not necessarily at the docs scan root
    # (e.g. --root examples), so resolve it by walking up from `root`.
    config_root = find_repo_root(root)
    cfg = load_config(config_root)
    docs = _docs_for(root, cluster)
    report = ConsistencyReport()

    report.findings += check_broken_cross_references(root, docs)
    report.findings += check_terminology(root, docs, cfg.get("canonical_terms", []))
    report.findings += check_time_sensitive(root, docs, cfg.get("time_sensitive_patterns", []))
    report.findings += check_structure_gaps(root, docs, cfg.get("expected_sections", {}))

    clusters: dict[str, list[Path]] = {}
    for d in docs:
        clusters.setdefault(d.parent.name, []).append(d)
    contradiction_findings, skipped = check_contradictions(clusters, config_root)
    report.findings += contradiction_findings
    report.llm_skipped = skipped

    return report
