from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_current_user, get_docs_root
from ..schemas import SearchResponse, SearchResult
from ..services.search import search_docs

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = "",
    cluster: str | None = None,
    status: str | None = None,
    doc_type: str | None = None,
    root=Depends(get_docs_root),
    _user=Depends(get_current_user),
):
    raw = search_docs(root, q, cluster=cluster, status=status, doc_type=doc_type)
    return SearchResponse(query=q, results=[SearchResult(**r) for r in raw])
