import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_research_kb.web.deps import get_app_root, get_docs_root
from ai_research_kb.web.main import app
from ai_research_kb.web.roles import Role
from ai_research_kb.web.users import upsert_user

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "examples"


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("WEB_JWT_SECRET", "test-secret-for-pytest-only-not-for-production-use")


@pytest.fixture
def users_root(tmp_path):
    upsert_user("admin1", "adminpass123", Role.admin, root=tmp_path)
    upsert_user("editor1", "editorpass123", Role.editor, root=tmp_path)
    upsert_user("viewer1", "viewerpass123", Role.viewer, root=tmp_path)
    return tmp_path


@pytest.fixture
def client(users_root):
    app.dependency_overrides[get_app_root] = lambda: users_root
    app.dependency_overrides[get_docs_root] = lambda: EXAMPLES_ROOT
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def writable_docs_root(tmp_path):
    """A disposable copy of examples/ — write endpoints must never mutate the real fixture."""
    dest = tmp_path / "docs"
    shutil.copytree(EXAMPLES_ROOT, dest)
    return dest


@pytest.fixture
def writable_client(users_root, writable_docs_root):
    app.dependency_overrides[get_app_root] = lambda: users_root
    app.dependency_overrides[get_docs_root] = lambda: writable_docs_root
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_header(client: TestClient, username: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
