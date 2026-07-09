from __future__ import annotations

from fastapi import APIRouter, Depends

from ...consistency import run_consistency_check
from ..deps import get_current_user, get_docs_root
from ..schemas import ConsistencyFindingOut, ConsistencyReportOut

router = APIRouter(tags=["consistency"])


@router.get("/consistency", response_model=ConsistencyReportOut)
def get_consistency(
    cluster: str | None = None,
    root=Depends(get_docs_root),
    _user=Depends(get_current_user),
):
    report = run_consistency_check(root, cluster=cluster)
    return ConsistencyReportOut(
        llm_skipped=report.llm_skipped,
        findings=[ConsistencyFindingOut(**f.__dict__) for f in report.findings],
    )
