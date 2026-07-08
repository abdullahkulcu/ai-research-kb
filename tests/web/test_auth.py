from conftest import auth_header


def test_login_success(client):
    r = client.post("/api/auth/login", json={"username": "admin1", "password": "adminpass123"})
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "admin"
    assert body["username"] == "admin1"
    assert body["access_token"]


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "admin1", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/api/auth/login", json={"username": "nope", "password": "x"})
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_token(client):
    headers = auth_header(client, "editor1", "editorpass123")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"username": "editor1", "role": "editor"}
