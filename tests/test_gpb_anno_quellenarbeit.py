"""Referenced-only GPB Quellenarbeit through the real worksheet/review seam."""
from __future__ import annotations

from datetime import date

from teachersaid.library import gpb_anno_quellenarbeit as anno
from teachersaid.library import gpb_anno_weltausstellung as anno2
from teachersaid.library import seed_anno_quellenarbeit, seed_anno_weltausstellung
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.resolve import resolve_grade
from teachersaid.pipeline.verify import verify
from teachersaid.store.repository import ReviewStore

TODAY = date(2026, 3, 1)


def test_anno_worksheet_is_referenced_only_and_verify_clean():
    content = anno.build_content()
    resolved = resolve_grade(anno.SUBJECT, anno.KLASSE, today=TODAY)
    assemble(content, resolved)
    report = verify(content, resolved)
    assert report.problems == []
    assert content.assets == []
    assert all(block.kind != "source_text" for block in content.iter_blocks())
    assert any(anno.ANNO_PAGE in str(block.content) for block in content.intro)
    tasks = [block for block in content.iter_blocks() if block.role == "task"]
    assert {serves.competence_id for task in tasks for serves in task.serves} <= {
        "GPB.US.3.ALL.02", "GPB.US.3.ALL.03", "GPB.US.3.ALL.07",
    }
    assert {"HME", "HOR"} <= {dim for task in tasks for dim in task.dimensions}


def test_seed_anno_worksheet_stages_pending_content(tmp_path):
    store = ReviewStore(tmp_path / "store")
    [item] = seed_anno_quellenarbeit(store, today=TODAY)
    assert item.source == "curated" and item.stage == "content" and item.status == "pending"
    assert item.error is None and item.verify_problems == []
    assert item.content and item.artifacts and item.artifacts.student_pdf


# --- the second ANNO Quellenarbeit: the official 1873 Weltausstellung voice ----
def test_weltausstellung_worksheet_is_referenced_only_and_verify_clean():
    content = anno2.build_content()
    resolved = resolve_grade(anno2.SUBJECT, anno2.KLASSE, today=TODAY)
    assemble(content, resolved)
    report = verify(content, resolved)
    assert report.problems == []
    assert content.assets == []                                   # referenced-only: no embeds
    assert all(block.kind != "source_text" for block in content.iter_blocks())
    assert any(anno2.ANNO_PAGE in str(block.content) for block in content.intro)
    tasks = [block for block in content.iter_blocks() if block.role == "task"]
    assert {serves.competence_id for task in tasks for serves in task.serves} <= {
        "GPB.US.3.ALL.02", "GPB.US.3.ALL.03", "GPB.US.3.ALL.07", "GPB.US.3.ALL.09",
    }
    assert {"HME", "HOR"} <= {dim for task in tasks for dim in task.dimensions}
    # the Standort task is the didactic point that distinguishes it from the 1871 sheet
    assert any("GPB.US.3.ALL.09" in {s.competence_id for s in t.serves} for t in tasks)


def test_seed_weltausstellung_stages_pending_content(tmp_path):
    store = ReviewStore(tmp_path / "store")
    [item] = seed_anno_weltausstellung(store, today=TODAY)
    assert item.source == "curated" and item.stage == "content" and item.status == "pending"
    assert item.error is None and item.verify_problems == []
    assert item.content and item.artifacts and item.artifacts.student_pdf
