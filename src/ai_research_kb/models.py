"""Pydantic models for frontmatter and the comment sidecar."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DocStatus(str, Enum):
    draft = "draft"
    review = "review"
    final = "final"
    archived = "archived"


class DocType(str, Enum):
    analysis = "analysis"
    design = "design"
    change_plan = "change-plan"
    notes = "notes"
    other = "other"


class Frontmatter(BaseModel):
    title: str
    cluster: str
    task_id: str | None = None
    task_url: str | None = None
    status: DocStatus
    doc_type: DocType
    tags: list[str] = Field(default_factory=list)
    related_docs: list[str] = Field(default_factory=list)
    version: int = 1
    created: date
    updated: date

    @field_validator("title", "cluster")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("boş olamaz")
        return v


class CommentStatus(str, Enum):
    open = "open"
    resolved = "resolved"


class Comment(BaseModel):
    id: str
    anchor: str
    author: str
    created: datetime
    body: str
    status: CommentStatus = CommentStatus.open
    thread: list["Comment"] = Field(default_factory=list)


Comment.model_rebuild()


class CommentFile(BaseModel):
    comments: list[Comment] = Field(default_factory=list)
