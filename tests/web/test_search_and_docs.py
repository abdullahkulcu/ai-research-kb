from conftest import auth_header


def test_search_requires_auth(client):
    r = client.get("/api/search", params={"q": "embedding"})
    assert r.status_code == 401


def test_search_finds_doc_and_surfaces_related_docs(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get("/api/search", params={"q": "embedding"}, headers=headers)
    assert r.status_code == 200
    results = r.json()["results"]
    assert results
    tasarim = next(res for res in results if res["doc"].endswith("tasarim.md"))
    assert "analiz.md" in tasarim["related_docs"]


def test_search_cluster_filter(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get(
        "/api/search",
        params={"q": "embedding", "cluster": "does-not-exist"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["results"] == []


def test_list_clusters(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get("/api/clusters", headers=headers)
    assert r.status_code == 200
    clusters = {c["cluster"] for c in r.json()}
    assert "rag-pipeline-degerlendirmesi" in clusters


def test_get_cluster_detail(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get("/api/clusters/rag-pipeline-degerlendirmesi", headers=headers)
    assert r.status_code == 200
    body = r.json()
    doc_names = {d["doc"] for d in body["docs"]}
    assert doc_names == {"analiz.md", "tasarim.md", "notlar.md"}
    assert body["cross_references"]["tasarim.md"] == ["analiz.md"]


def test_get_doc(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get(
        "/api/docs/rag-pipeline-degerlendirmesi/analiz.md", headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "RAG Pipeline Değerlendirmesi - Analiz"
    assert "## Özet" in body["body"]


def test_get_doc_404(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get(
        "/api/docs/rag-pipeline-degerlendirmesi/olmayan.md", headers=headers
    )
    assert r.status_code == 404
