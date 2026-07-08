"""Minimal task-plan.yaml generation + safe editing.

This is a deliberately small slice of the original Faz 3 plan (flow.yaml,
dependency inference, code-impact analysis are NOT implemented here). It only
extracts numbered action items under a configured heading (default
"Yapılacaklar") from each doc in a cluster, and lets an editor+ edit/approve
them from the panel. Re-generating never removes or overwrites existing tasks —
only new ones (by stable id) are appended.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from ...repo import find_docs, parse_markdown

_ITEM_RE = re.compile(r"^\s*\d+\.\s+(.*\S)\s*$")
_EFFORT_RE = re.compile(r"\(effort:\s*([A-Za-z0-9]+)\)", re.IGNORECASE)


def task_plan_path(cluster_dir: Path) -> Path:
    return cluster_dir / "task-plan.yaml"


def load_task_plan(cluster_dir: Path) -> list[dict[str, Any]]:
    path = task_plan_path(cluster_dir)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("tasks", [])


def save_task_plan(cluster_dir: Path, tasks: list[dict[str, Any]]) -> None:
    path = task_plan_path(cluster_dir)
    path.write_text(
        yaml.safe_dump({"tasks": tasks}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _stable_id(source_doc: str, text: str) -> str:
    digest = hashlib.sha1(f"{source_doc}:{text}".encode("utf-8")).hexdigest()
    return digest[:10]


def _extract_from_doc(root: Path, path: Path, heading: str) -> list[dict[str, Any]]:
    try:
        doc = parse_markdown(path)
    except ValueError:
        return []

    lines = doc.body.splitlines()
    heading_re = re.compile(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$", re.IGNORECASE)
    in_section = False
    extracted: list[dict[str, Any]] = []
    rel_doc = str(path.relative_to(root))

    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            in_section = bool(heading_re.match(line))
            continue
        if not in_section:
            continue
        m = _ITEM_RE.match(line)
        if not m:
            continue
        text = m.group(1)
        effort_m = _EFFORT_RE.search(text)
        title = _EFFORT_RE.sub("", text).strip().rstrip(".").strip()
        extracted.append(
            {
                "id": _stable_id(rel_doc, text),
                "title": title,
                "description": text,
                "source_doc": rel_doc,
                "source_section": heading,
                "effort": effort_m.group(1) if effort_m else None,
                "depends_on": [],
                "status": "proposed",
                "task_ref": None,
                "task_url": None,
            }
        )
    return extracted


def generate_tasks(root: Path, cluster_dir: Path, heading: str) -> list[dict[str, Any]]:
    """Extract action items and merge (idempotent, non-destructive) into task-plan.yaml."""
    existing = load_task_plan(cluster_dir)
    existing_ids = {t["id"] for t in existing}

    docs = [d for d in find_docs(root) if d.parent == cluster_dir]
    new_tasks: list[dict[str, Any]] = []
    for doc_path in docs:
        for task in _extract_from_doc(root, doc_path, heading):
            if task["id"] not in existing_ids:
                new_tasks.append(task)
                existing_ids.add(task["id"])

    merged = existing + new_tasks
    save_task_plan(cluster_dir, merged)
    return merged


_ALLOWED_STATUSES = {"proposed", "approved"}
_PATCHABLE_FIELDS = {"title", "description", "effort", "depends_on", "status"}


def patch_task(cluster_dir: Path, task_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    tasks = load_task_plan(cluster_dir)
    for task in tasks:
        if task["id"] == task_id:
            for key, value in patch.items():
                if value is None or key not in _PATCHABLE_FIELDS:
                    continue
                if key == "status" and value not in _ALLOWED_STATUSES:
                    raise ValueError(f"geçersiz status: {value!r}")
                task[key] = value
            save_task_plan(cluster_dir, tasks)
            return task
    raise KeyError(f"task bulunamadı: {task_id}")
