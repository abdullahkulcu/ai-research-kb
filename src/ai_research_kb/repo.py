"""Repo-level helpers: finding docs, locating the repo root, parsing markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.MULTILINE)


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upward from `start` (default: cwd) looking for pyproject.toml."""
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return p


@dataclass
class ParsedDoc:
    path: Path
    frontmatter_raw: dict
    body: str

    def headings(self, level: int | None = None) -> list[str]:
        out = []
        for m in HEADING_RE.finditer(self.body):
            hlevel = len(m.group(1))
            if level is None or hlevel == level:
                out.append(m.group(2).strip())
        return out


def parse_markdown(path: Path) -> ParsedDoc:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path}: frontmatter (--- ... ---) bulunamadı")
    fm_raw = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm_raw, dict):
        raise ValueError(f"{path}: frontmatter bir YAML sözlüğü olmalı")
    body = text[m.end() :]
    return ParsedDoc(path=path, frontmatter_raw=fm_raw, body=body)


def find_docs(root: Path) -> list[Path]:
    """All research documents under `root` — everything except folder-level READMEs."""
    if not root.exists():
        return []
    return sorted(
        p
        for p in root.rglob("*.md")
        if p.name.lower() != "readme.md" and not p.name.endswith(".comments.md")
    )
