"""FastAPI app: REST layer over the ai_research_kb library.

Run with `ai-research-kb serve` (see cli.py) or `uvicorn ai_research_kb.web.main:app`.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import load_config
from ..repo import find_repo_root
from .routers import auth, clickup, comments, consistency, docs, search, tasks

app = FastAPI(title="ai-research-kb API", version="0.1.0")

_cfg = load_config(find_repo_root())
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cfg["web"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    search.router,
    docs.router,
    comments.router,
    consistency.router,
    tasks.router,
    clickup.router,
):
    app.include_router(router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
