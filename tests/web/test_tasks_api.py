from conftest import auth_header

CLUSTER = "rag-pipeline-degerlendirmesi"


def test_generate_tasks_extracts_from_notlar(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    r = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers)
    assert r.status_code == 200
    tasks = r.json()
    assert len(tasks) == 3
    titles = {t["title"] for t in tasks}
    assert "Çok dilli embedding modelini seç" in titles
    efforts = {t["effort"] for t in tasks}
    assert efforts == {"M", "L", "S"}
    assert all(t["status"] == "proposed" for t in tasks)


def test_generate_tasks_is_idempotent(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    first = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    second = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    assert len(first) == len(second) == 3
    assert {t["id"] for t in first} == {t["id"] for t in second}


def test_generate_preserves_edits_on_regenerate(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    tasks = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    task_id = tasks[0]["id"]

    patched = writable_client.patch(
        f"/api/tasks/{CLUSTER}/{task_id}", json={"status": "approved"}, headers=headers
    ).json()
    assert patched["status"] == "approved"

    regenerated = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    still_approved = next(t for t in regenerated if t["id"] == task_id)
    assert still_approved["status"] == "approved"


def test_approve_task(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    tasks = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    task_id = tasks[1]["id"]

    r = writable_client.post(f"/api/tasks/{CLUSTER}/{task_id}/approve", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_patch_unknown_task_returns_404(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    r = writable_client.patch(
        f"/api/tasks/{CLUSTER}/does-not-exist", json={"status": "approved"}, headers=headers
    )
    assert r.status_code == 404


def test_patch_invalid_status_returns_400(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    tasks = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    task_id = tasks[0]["id"]

    r = writable_client.patch(
        f"/api/tasks/{CLUSTER}/{task_id}", json={"status": "not-a-status"}, headers=headers
    )
    assert r.status_code == 400


def test_get_tasks_before_generate_is_empty(writable_client):
    headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.get(f"/api/tasks/{CLUSTER}", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


def test_viewer_cannot_generate_tasks(writable_client):
    headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers)
    assert r.status_code == 403


def test_viewer_cannot_patch_or_approve_task(writable_client):
    editor_headers = auth_header(writable_client, "editor1", "editorpass123")
    tasks = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=editor_headers).json()
    task_id = tasks[0]["id"]

    viewer_headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.patch(
        f"/api/tasks/{CLUSTER}/{task_id}", json={"status": "approved"}, headers=viewer_headers
    )
    assert r.status_code == 403

    r = writable_client.post(
        f"/api/tasks/{CLUSTER}/{task_id}/approve", headers=viewer_headers
    )
    assert r.status_code == 403


def test_admin_can_generate_and_approve_tasks(writable_client):
    headers = auth_header(writable_client, "admin1", "adminpass123")
    tasks = writable_client.post(f"/api/tasks/{CLUSTER}/generate", headers=headers).json()
    task_id = tasks[0]["id"]

    r = writable_client.post(f"/api/tasks/{CLUSTER}/{task_id}/approve", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
