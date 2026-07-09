"""Request/response models for the REST API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from ..models import CommentStatus, DocStatus, DocType
from .roles import Role


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: Role


class MeResponse(BaseModel):
    username: str
    role: Role


class SearchResult(BaseModel):
    cluster: str
    doc: str
    title: str
    snippet: str
    score: int
    related_docs: list[str] = []


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class ClusterSummary(BaseModel):
    cluster: str
    doc_count: int
    docs: list[str]


class DocSummary(BaseModel):
    doc: str
    title: str
    status: DocStatus
    doc_type: DocType


class ClusterDetail(BaseModel):
    cluster: str
    docs: list[DocSummary]
    cross_references: dict[str, list[str]]


class DocResponse(BaseModel):
    cluster: str
    doc: str
    title: str
    status: DocStatus
    doc_type: DocType
    tags: list[str]
    related_docs: list[str]
    version: int
    created: date
    updated: date
    task_id: str | None = None
    task_url: str | None = None
    body: str


class CommentIn(BaseModel):
    anchor: str
    body: str


class CommentOut(BaseModel):
    id: str
    anchor: str
    author: str
    created: datetime
    body: str
    status: CommentStatus
    thread: list["CommentOut"] = []


CommentOut.model_rebuild()


class ConsistencyFindingOut(BaseModel):
    category: str
    severity: str
    cluster: str
    doc: str
    message: str


class ConsistencyReportOut(BaseModel):
    llm_skipped: bool
    findings: list[ConsistencyFindingOut]


class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    source_doc: str
    source_section: str
    effort: str | None = None
    depends_on: list[str] = []
    status: str = "proposed"
    task_ref: str | None = None
    task_url: str | None = None


class TaskPatchIn(BaseModel):
    title: str | None = None
    description: str | None = None
    effort: str | None = None
    depends_on: list[str] | None = None
    status: str | None = None


class ClickUpPushRequest(BaseModel):
    dry_run: bool = True


class ClickUpPushResult(BaseModel):
    id: str
    title: str
    action: str  # "would_create" | "created" | "skip"
    task_ref: str | None = None
    task_url: str | None = None
