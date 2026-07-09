from conftest import auth_header

CLUSTER = "rag-pipeline-degerlendirmesi"
DOC = "tasarim.md"


def test_list_seeded_comments(writable_client):
    headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.get(f"/api/docs/{CLUSTER}/{DOC}/comments", headers=headers)
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()}
    assert {"c1a2b3c4", "d4e5f6a7"} <= ids


def test_add_comment_with_valid_anchor(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments",
        json={"anchor": "Riskler", "body": "yeni yorum"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["author"] == "editor1"
    assert body["status"] == "open"

    listed = writable_client.get(f"/api/docs/{CLUSTER}/{DOC}/comments", headers=headers).json()
    assert any(c["body"] == "yeni yorum" for c in listed)


def test_add_comment_with_invalid_anchor_returns_400(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments",
        json={"anchor": "olmayan-baslik", "body": "x"},
        headers=headers,
    )
    assert r.status_code == 400


def test_resolve_comment(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments/c1a2b3c4/resolve", headers=headers
    )
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


def test_resolve_unknown_comment_returns_404(writable_client):
    headers = auth_header(writable_client, "editor1", "editorpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments/does-not-exist/resolve", headers=headers
    )
    assert r.status_code == 404


def test_viewer_cannot_add_comment(writable_client):
    headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments",
        json={"anchor": "Riskler", "body": "viewer yorumu"},
        headers=headers,
    )
    assert r.status_code == 403


def test_viewer_cannot_resolve_comment(writable_client):
    headers = auth_header(writable_client, "viewer1", "viewerpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments/c1a2b3c4/resolve", headers=headers
    )
    assert r.status_code == 403


def test_admin_can_add_comment(writable_client):
    headers = auth_header(writable_client, "admin1", "adminpass123")
    r = writable_client.post(
        f"/api/docs/{CLUSTER}/{DOC}/comments",
        json={"anchor": "Riskler", "body": "admin yorumu"},
        headers=headers,
    )
    assert r.status_code == 200
