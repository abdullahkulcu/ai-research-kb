from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...comments import add_comment, list_comments, resolve_comment
from ..deps import get_current_user, get_docs_root
from ..schemas import CommentIn, CommentOut

router = APIRouter(tags=["comments"])


def _doc_path(root, cluster: str, doc: str):
    path = root / cluster / doc
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"doküman bulunamadı: {cluster}/{doc}")
    return path


@router.get("/docs/{cluster}/{doc}/comments", response_model=list[CommentOut])
def get_comments(
    cluster: str, doc: str, root=Depends(get_docs_root), user=Depends(get_current_user)
):
    path = _doc_path(root, cluster, doc)
    return [CommentOut(**c.model_dump()) for c in list_comments(path)]


@router.post("/docs/{cluster}/{doc}/comments", response_model=CommentOut)
def post_comment(
    cluster: str,
    doc: str,
    payload: CommentIn,
    root=Depends(get_docs_root),
    user=Depends(get_current_user),
):
    path = _doc_path(root, cluster, doc)
    try:
        comment = add_comment(path, payload.anchor, payload.body, user.username)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    return CommentOut(**comment.model_dump())


@router.post("/docs/{cluster}/{doc}/comments/{comment_id}/resolve", response_model=CommentOut)
def resolve_comment_route(
    cluster: str,
    doc: str,
    comment_id: str,
    root=Depends(get_docs_root),
    user=Depends(get_current_user),
):
    path = _doc_path(root, cluster, doc)
    try:
        comment = resolve_comment(path, comment_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    return CommentOut(**comment.model_dump())
