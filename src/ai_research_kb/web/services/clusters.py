from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status

from ...repo import find_docs


def cluster_dir(root: Path, cluster: str) -> Path:
    for path in find_docs(root):
        if path.parent.name == cluster:
            return path.parent
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"cluster bulunamadı: {cluster}")
