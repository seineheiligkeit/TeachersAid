"""The master-library examples must build, assemble, verify clean, and render.

This locks the curated 'great worksheet' examples against catalog drift: if a
competence ID, dimension code, or task kind stops matching the catalog/subject
model, these fail loudly.
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library import EXAMPLES, find, seed_library
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.resolve import resolve
from teachersaid.pipeline.verify import verify
from teachersaid.schema.worksheet import BundleRequest, WorksheetContent
from teachersaid.store.repository import ReviewStore

IN_WINDOW = date(2026, 3, 1)


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda e: e.key)
def test_example_builds_assembles_and_verifies_clean(ex):
    content = ex.build()
    assert isinstance(content, WorksheetContent)
    res = resolve(
        BundleRequest(subject=ex.subject, klasse=ex.klasse, topic_raw=ex.topic),
        today=IN_WINDOW,
    )
    assert res.grade_check is True  # the example's subject/grade is catalog-valid
    assemble(content, res)
    report = verify(content, res)
    assert report.problems == [], (ex.key, report.problems)  # warnings are allowed
    assert content.nachweis is not None and content.depth_profile is not None


def test_find_matches_registered_examples():
    assert find("Physik", "Strahlung und Radioaktivität").key == "phy-strahlung"
    assert find("Biologie", "Immunsystem und Impfungen").key == "bio-immunsystem"
    assert find("Chemie", "irgendwas") is None


def test_seed_library_populates_review_queue(tmp_path):
    store = ReviewStore(tmp_path / "store")
    items = seed_library(store, today=IN_WINDOW)
    assert len(items) == len(EXAMPLES)
    # each lands as a pending content item with rendered artifacts and no error
    for it in items:
        assert it.stage == "content" and it.status == "pending", it.error
        assert it.error is None, it.error
        assert it.artifacts and it.artifacts.student_pdf and it.artifacts.teacher_pdf
