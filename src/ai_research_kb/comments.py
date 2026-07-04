"""Comment sidecar (<doc>.comments.yaml): CRUD + anchor validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .models import Comment, CommentFile, CommentStatus
from .repo import parse_markdown


def comments_path_for(doc_path: Path) -> Path:
    return doc_path.with_name(doc_path.stem + ".comments.yaml")


def load_comments(doc_path: Path) -> CommentFile:
    cpath = comments_path_for(doc_path)
    if not cpath.exists():
        return CommentFile()
    data = yaml.safe_load(cpath.read_text(encoding="utf-8")) or {}
    return CommentFile.model_validate(data)


def save_comments(doc_path: Path, cfile: CommentFile) -> None:
    cpath = comments_path_for(doc_path)
    data = cfile.model_dump(mode="json")
    cpath.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def anchor_exists(doc_path: Path, anchor: str) -> bool:
    doc = parse_markdown(doc_path)
    headings = {h.lower() for h in doc.headings()}
    if anchor.strip().lower() in headings:
        return True
    return anchor.strip() in doc.body


def add_comment(doc_path: Path, anchor: str, body: str, author: str) -> Comment:
    if not anchor_exists(doc_path, anchor):
        raise ValueError(f"anchor bulunamadı: {anchor!r} ({doc_path})")
    cfile = load_comments(doc_path)
    comment = Comment(
        id=uuid.uuid4().hex[:8],
        anchor=anchor,
        author=author,
        created=datetime.now(timezone.utc),
        body=body,
        status=CommentStatus.open,
    )
    cfile.comments.append(comment)
    save_comments(doc_path, cfile)
    return comment


def list_comments(doc_path: Path, status: CommentStatus | None = None) -> list[Comment]:
    cfile = load_comments(doc_path)
    if status is None:
        return cfile.comments
    return [c for c in cfile.comments if c.status == status]


def _find_comment(comments: list[Comment], comment_id: str) -> Comment | None:
    for c in comments:
        if c.id == comment_id:
            return c
        found = _find_comment(c.thread, comment_id)
        if found:
            return found
    return None


def resolve_comment(doc_path: Path, comment_id: str) -> Comment:
    cfile = load_comments(doc_path)
    comment = _find_comment(cfile.comments, comment_id)
    if comment is None:
        raise ValueError(f"yorum bulunamadı: {comment_id}")
    comment.status = CommentStatus.resolved
    save_comments(doc_path, cfile)
    return comment


def check_broken_anchors(doc_path: Path) -> list[str]:
    """Return ids of comments (including thread replies) whose anchor no longer exists."""
    cfile = load_comments(doc_path)
    broken: list[str] = []

    def walk(comments: list[Comment]) -> None:
        for c in comments:
            if not anchor_exists(doc_path, c.anchor):
                broken.append(c.id)
            walk(c.thread)

    walk(cfile.comments)
    return broken
