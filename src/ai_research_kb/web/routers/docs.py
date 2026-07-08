from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...models import Frontmatter
from ...repo import find_docs, parse_markdown
from ..deps import get_current_user, get_docs_root
from ..schemas import ClusterDetail, ClusterSummary, DocResponse, DocSummary
from ..services.clusters import cluster_dir as resolve_cluster_dir

router = APIRouter(tags=["docs"])


@router.get("/clusters", response_model=list[ClusterSummary])
def list_clusters(root=Depends(get_docs_root), _user=Depends(get_current_user)):
    by_cluster: dict[str, list[str]] = {}
    for path in find_docs(root):
        by_cluster.setdefault(path.parent.name, []).append(str(path.relative_to(root)))
    return [
        ClusterSummary(cluster=c, doc_count=len(docs), docs=sorted(docs))
        for c, docs in sorted(by_cluster.items())
    ]


@router.get("/clusters/{cluster}", response_model=ClusterDetail)
def get_cluster(cluster: str, root=Depends(get_docs_root), _user=Depends(get_current_user)):
    cdir = resolve_cluster_dir(root, cluster)
    docs: list[DocSummary] = []
    cross_refs: dict[str, list[str]] = {}
    for path in sorted(cdir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            parsed = parse_markdown(path)
            fm = Frontmatter.model_validate(parsed.frontmatter_raw)
        except ValueError:
            continue
        docs.append(DocSummary(doc=path.name, title=fm.title, status=fm.status, doc_type=fm.doc_type))
        cross_refs[path.name] = fm.related_docs
    return ClusterDetail(cluster=cluster, docs=docs, cross_references=cross_refs)


@router.get("/docs/{cluster}/{doc}", response_model=DocResponse)
def get_doc(
    cluster: str, doc: str, root=Depends(get_docs_root), _user=Depends(get_current_user)
):
    path = root / cluster / doc
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"doküman bulunamadı: {cluster}/{doc}")
    parsed = parse_markdown(path)
    fm = Frontmatter.model_validate(parsed.frontmatter_raw)
    return DocResponse(
        cluster=cluster, doc=doc, body=parsed.body, **fm.model_dump(exclude={"cluster"})
    )
