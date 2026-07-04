from ai_research_kb.consistency import run_consistency_check


def test_broken_cross_reference_detected(examples_root):
    report = run_consistency_check(examples_root, cluster="rag-pipeline-degerlendirmesi")
    broken = report.by_category().get("broken-cross-reference", [])
    messages = " ".join(f.message for f in broken)
    assert "arsiv/eski-analiz.md" in messages
    # both the related_docs entry and the inline link should be caught
    assert len(broken) >= 2


def test_terminology_alias_detected(examples_root):
    report = run_consistency_check(examples_root, cluster="rag-pipeline-degerlendirmesi")
    terms = report.by_category().get("terminology", [])
    messages = " ".join(f.message for f in terms)
    assert "büyük dil modeli" in messages
    assert "yeniden sıralama" in messages


def test_time_sensitive_claims_detected(examples_root):
    report = run_consistency_check(examples_root, cluster="rag-pipeline-degerlendirmesi")
    findings = report.by_category().get("time-sensitive", [])
    assert findings, "zamana duyarlı en az bir ifade tespit edilmeliydi"


def test_structure_gap_detected_for_design_doc(examples_root):
    report = run_consistency_check(examples_root, cluster="rag-pipeline-degerlendirmesi")
    gaps = report.by_category().get("structure-gap", [])
    messages = " ".join(f.message for f in gaps if "tasarim.md" in f.doc)
    assert "Alternatifler" in messages


def test_llm_skipped_without_provider(examples_root):
    report = run_consistency_check(examples_root, cluster="rag-pipeline-degerlendirmesi")
    assert report.llm_skipped is True
    assert "contradiction-candidate" not in report.by_category()
