from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...config import load_config
from ...repo import find_repo_root
from ..deps import get_current_user, get_docs_root, require_role
from ..roles import Role
from ..schemas import TaskOut, TaskPatchIn
from ..services.clusters import cluster_dir as resolve_cluster_dir
from ..services.tasks import generate_tasks, load_task_plan, patch_task

router = APIRouter(tags=["tasks"])


@router.get("/tasks/{cluster}", response_model=list[TaskOut])
def get_tasks(cluster: str, root=Depends(get_docs_root), _user=Depends(get_current_user)):
    cdir = resolve_cluster_dir(root, cluster)
    return [TaskOut(**t) for t in load_task_plan(cdir)]


@router.post("/tasks/{cluster}/generate", response_model=list[TaskOut])
def post_generate_tasks(
    cluster: str, root=Depends(get_docs_root), _user=Depends(require_role(Role.editor))
):
    cdir = resolve_cluster_dir(root, cluster)
    heading = load_config(find_repo_root(root))["web"]["task_extraction"]["heading"]
    tasks = generate_tasks(root, cdir, heading)
    return [TaskOut(**t) for t in tasks]


@router.patch("/tasks/{cluster}/{task_id}", response_model=TaskOut)
def patch_task_route(
    cluster: str,
    task_id: str,
    payload: TaskPatchIn,
    root=Depends(get_docs_root),
    _user=Depends(require_role(Role.editor)),
):
    cdir = resolve_cluster_dir(root, cluster)
    try:
        task = patch_task(cdir, task_id, payload.model_dump(exclude_unset=True))
    except KeyError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    return TaskOut(**task)


@router.post("/tasks/{cluster}/{task_id}/approve", response_model=TaskOut)
def approve_task_route(
    cluster: str,
    task_id: str,
    root=Depends(get_docs_root),
    _user=Depends(require_role(Role.editor)),
):
    cdir = resolve_cluster_dir(root, cluster)
    try:
        task = patch_task(cdir, task_id, {"status": "approved"})
    except KeyError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    return TaskOut(**task)
