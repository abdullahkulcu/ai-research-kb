from ai_research_kb.frontmatter import validate_tree


def test_examples_cluster_has_no_schema_errors(examples_root):
    results = validate_tree(examples_root)
    assert results, "beklenen dokümanlar bulunamadı"

    errors = [
        issue
        for _fm, issues in results.values()
        for issue in issues
        if issue.severity == "error"
    ]
    assert errors == [], f"beklenmeyen kritik hata(lar): {errors}"


def test_frontmatter_parses_expected_docs(cluster_dir):
    results = validate_tree(cluster_dir)
    names = {p.name for p in results}
    assert names == {"analiz.md", "tasarim.md", "notlar.md"}
    for fm, _issues in results.values():
        assert fm is not None
        assert fm.cluster == "rag-pipeline-degerlendirmesi"


def test_cluster_mismatch_is_flagged(tmp_path):
    cluster_dir = tmp_path / "gercek-klasor"
    cluster_dir.mkdir()
    (cluster_dir / "doc.md").write_text(
        """---
title: Test
cluster: yanlis-klasor
status: draft
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

# Test
""",
        encoding="utf-8",
    )
    results = validate_tree(tmp_path)
    _fm, issues = next(iter(results.values()))
    codes = {i.code for i in issues}
    assert "cluster-mismatch" in codes


def test_invalid_status_is_a_schema_error(tmp_path):
    cluster_dir = tmp_path / "c"
    cluster_dir.mkdir()
    (cluster_dir / "doc.md").write_text(
        """---
title: Test
cluster: c
status: not-a-real-status
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

# Test
""",
        encoding="utf-8",
    )
    results = validate_tree(tmp_path)
    fm, issues = next(iter(results.values()))
    assert fm is None
    assert any(i.severity == "error" and i.code == "frontmatter-schema" for i in issues)
