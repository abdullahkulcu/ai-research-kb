import pytest

from ai_research_kb.comments import (
    add_comment,
    check_broken_anchors,
    list_comments,
    resolve_comment,
)
from ai_research_kb.models import CommentStatus


def test_existing_comments_have_no_broken_anchors(cluster_dir):
    doc = cluster_dir / "tasarim.md"
    assert check_broken_anchors(doc) == []


def test_list_comments_returns_seeded_comments(cluster_dir):
    doc = cluster_dir / "tasarim.md"
    comments = list_comments(doc)
    ids = {c.id for c in comments}
    assert {"c1a2b3c4", "d4e5f6a7"} <= ids

    open_comments = list_comments(doc, CommentStatus.open)
    assert {c.id for c in open_comments} == {"c1a2b3c4"}


def test_add_comment_with_valid_heading_anchor(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(
        """---
title: T
cluster: tmp_path
status: draft
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

## Bir Bolum
metin
""",
        encoding="utf-8",
    )
    comment = add_comment(doc, "Bir Bolum", "yorum govdesi", "yazar")
    assert comment.status == CommentStatus.open

    loaded = list_comments(doc)
    assert len(loaded) == 1
    assert loaded[0].body == "yorum govdesi"


def test_add_comment_with_invalid_anchor_raises(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(
        """---
title: T
cluster: tmp_path
status: draft
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

## Bir Bolum
metin
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        add_comment(doc, "olmayan-baslik", "govde", "yazar")


def test_resolve_comment_persists(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(
        """---
title: T
cluster: tmp_path
status: draft
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

## Bolum
metin
""",
        encoding="utf-8",
    )
    comment = add_comment(doc, "Bolum", "govde", "yazar")
    resolve_comment(doc, comment.id)

    reloaded = list_comments(doc)
    assert reloaded[0].status == CommentStatus.resolved


def test_broken_anchor_detected_after_heading_removed(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(
        """---
title: T
cluster: tmp_path
status: draft
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

## Silinecek Bolum
metin
""",
        encoding="utf-8",
    )
    add_comment(doc, "Silinecek Bolum", "govde", "yazar")

    doc.write_text(
        """---
title: T
cluster: tmp_path
status: draft
doc_type: notes
created: 2026-01-01
updated: 2026-01-01
---

## Yeni Bolum
metin
""",
        encoding="utf-8",
    )
    assert len(check_broken_anchors(doc)) == 1
