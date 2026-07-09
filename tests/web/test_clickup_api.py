from conftest import auth_header

import ai_research_kb.web.routers.clickup as clickup_router
import ai_research_kb.web.services.clickup as clickup_service

CLUSTER = "rag-pipeline-degerlendirmesi"


def _approve_first_task(client, headers):
    tasks = client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    task_id = tasks[0]["id"]
    client.post(f"/api/tasks/{CLUSTER}/{task_id}/approve", headers=headers)
    return task_id


def test_dry_run_does_not_require_token_or_list_id(writable_client, monkeypatch):
    monkeypatch.delenv("CLICKUP_API_TOKEN", raising=False)
    headers = auth_header(writable_client, "editor1", "editorpass123")
    _approve_first_task(writable_client, headers)

    r = writable_client.post(
        f"/api/tasks/{CLUSTER}/clickup/push", json={"dry_run": True}, headers=headers
    )
    assert r.status_code == 200
    results = r.json()
    assert any(res["action"] == "would_create" for res in results)


def test_real_push_without_token_returns_400(writable_client, monkeypatch):
    monkeypatch.delenv("CLICKUP_API_TOKEN", raising=False)
    headers = auth_header(writable_client, "editor1", "editorpass123")
    _approve_first_task(writable_client, headers)

    r = writable_client.post(
        f"/api/tasks/{CLUSTER}/clickup/push", json={"dry_run": False}, headers=headers
    )
    assert r.status_code == 400
    assert "CLICKUP_API_TOKEN" in r.json()["detail"]


def test_real_push_without_list_id_returns_400(writable_client, monkeypatch):
    monkeypatch.setenv("CLICKUP_API_TOKEN", "tok")
    headers = auth_header(writable_client, "editor1", "editorpass123")
    _approve_first_task(writable_client, headers)

    r = writable_client.post(
        f"/api/tasks/{CLUSTER}/clickup/push", json={"dry_run": False}, headers=headers
    )
    assert r.status_code == 400
    assert "list_id" in r.json()["detail"]


def test_viewer_cannot_push_to_clickup(writable_client):
    editor_headers = auth_header(writable_client, "editor1", "editorpass123")
    _approve_first_task(writable_client, editor_headers)

    viewer_headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.post(
        f"/api/tasks/{CLUSTER}/clickup/push", json={"dry_run": True}, headers=viewer_headers
    )
    assert r.status_code == 403


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, *, json, headers):
        self.calls.append(json)
        return self.responses.pop(0)

    def close(self):
        pass


def test_real_push_end_to_end_writes_task_ref_and_is_idempotent(
    writable_client, monkeypatch
):
    monkeypatch.setenv("CLICKUP_API_TOKEN", "tok")
    monkeypatch.setattr(
        clickup_router, "load_config", lambda root: {"clickup": {"list_id": "555"}}
    )
    fake = _FakeClient([_FakeResponse(200, {"id": 42, "url": "https://app.clickup.com/t/42"})])
    monkeypatch.setattr(clickup_service, "_real_client", lambda: fake)

    headers = auth_header(writable_client, "editor1", "editorpass123")
    task_id = _approve_first_task(writable_client, headers)

    r = writable_client.post(
        f"/api/tasks/{CLUSTER}/clickup/push", json={"dry_run": False}, headers=headers
    )
    assert r.status_code == 200
    results = r.json()
    created = next(res for res in results if res["id"] == task_id)
    assert created["action"] == "created"
    assert created["task_ref"] == "42"
    assert created["task_url"] == "https://app.clickup.com/t/42"
    assert len(fake.calls) == 1

    # task-plan.yaml on disk now carries the task_ref
    tasks = writable_client.get(f"/api/tasks/{CLUSTER}", headers=headers).json()
    pushed = next(t for t in tasks if t["id"] == task_id)
    assert pushed["task_ref"] == "42"

    # re-running must skip (idempotent) and make no new HTTP call
    r2 = writable_client.post(
        f"/api/tasks/{CLUSTER}/clickup/push", json={"dry_run": False}, headers=headers
    )
    results2 = r2.json()
    skipped = next(res for res in results2 if res["id"] == task_id)
    assert skipped["action"] == "skip"
    assert len(fake.calls) == 1  # unchanged — no second HTTP call
