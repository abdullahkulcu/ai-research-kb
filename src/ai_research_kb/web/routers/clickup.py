"""ClickUp push (Faz 2): explicit dry-run before any real external mutation."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status

from ...config import load_config
from ...repo import find_repo_root
from ..deps import get_docs_root, require_role
from ..roles import Role
from ..schemas import ClickUpPushRequest, ClickUpPushResult
from ..services.clickup import ClickUpError, push_tasks
from ..services.clusters import cluster_dir as resolve_cluster_dir
from ..services.tasks import load_task_plan, save_task_plan

router = APIRouter(tags=["clickup"])


@router.post("/tasks/{cluster}/clickup/push", response_model=list[ClickUpPushResult])
def clickup_push(
    cluster: str,
    payload: ClickUpPushRequest,
    root=Depends(get_docs_root),
    _user=Depends(require_role(Role.editor)),
):
    cdir = resolve_cluster_dir(root, cluster)
    tasks = load_task_plan(cdir)

    list_id = load_config(find_repo_root(root)).get("clickup", {}).get("list_id")
    token = os.environ.get("CLICKUP_API_TOKEN")

    if not payload.dry_run:
        if not token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "CLICKUP_API_TOKEN tanımlı değil (.env)")
        if not list_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "config.yaml: clickup.list_id tanımlı değil"
            )

    try:
        results = push_tasks(
            tasks,
            list_id=str(list_id) if list_id else "",
            token=token or "",
            dry_run=payload.dry_run,
        )
    except ClickUpError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e)) from e

    if not payload.dry_run:
        save_task_plan(cdir, tasks)

    return results
