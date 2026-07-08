from conftest import auth_header


def test_consistency_report_shape(client):
    headers = auth_header(client, "viewer1", "viewerpass123")
    r = client.get(
        "/api/consistency",
        params={"cluster": "rag-pipeline-degerlendirmesi"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["llm_skipped"] is True
    categories = {f["category"] for f in body["findings"]}
    assert {"broken-cross-reference", "terminology", "time-sensitive", "structure-gap"} <= categories
