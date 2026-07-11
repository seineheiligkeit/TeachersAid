"""Historical ImageSource: rights/store gate and annotation-derived worksheet."""

from __future__ import annotations

from datetime import date
import hashlib

import pytest
from PIL import Image

from teachersaid.library.image_sources import ISABEY_WIENER_KONGRESS, find_image_source
from teachersaid.schema.image_sources import ImageSource, ReproductionRights

TODAY = date(2026, 7, 11)


def _fixture_record(tmp_path):
    from teachersaid.pipeline.image_sources import ingest_image_source
    from teachersaid.store.imagesourcestore import ImageSourceStore

    file = tmp_path / "source.jpg"
    Image.new("RGB", (640, 480), "white").save(file, format="JPEG")
    sha1 = hashlib.sha1(file.read_bytes()).hexdigest()  # noqa: S324 - file identity
    ref = ISABEY_WIENER_KONGRESS.source.model_copy(
        update={"width": 640, "height": 480, "sha1": sha1}
    )
    image = ISABEY_WIENER_KONGRESS.model_copy(update={"source": ref})
    store = ImageSourceStore(tmp_path / "image_sources")
    return store, ingest_image_source(store, image, file=file, today=TODAY)


def test_flagship_has_complete_ordered_ladder_and_cross_asset_links():
    image = ISABEY_WIENER_KONGRESS
    assert [a.kind for a in image.annotations] == ["beschreibung", "analyse", "interpretation"]
    assert image.related_sachverhalt_id == "sv-wiener-kongress"
    assert image.related_text_id == "deu-anno-lehrertag-1871"
    assert find_image_source(image.id) is image
    assert image.source.is_clear(2026) == (True, [])


def test_ladder_is_required_and_rights_layers_fail_independently():
    with pytest.raises(ValueError, match="all three"):
        ImageSource.model_validate(
            ISABEY_WIENER_KONGRESS.model_dump() | {
                "annotations": [ISABEY_WIENER_KONGRESS.annotations[0].model_dump()]
            }
        )
    unclear = ISABEY_WIENER_KONGRESS.source.model_copy(
        update={
            "reproduction_rights": ReproductionRights(
                basis="public_domain_mark", licence="public domain", attribution_required=False,
                evidence="A generic claim without a Public Domain Mark.",
            )
        }
    )
    ok, reasons = unclear.is_clear(2026)
    assert not ok and any(reason.startswith("reproduction:") for reason in reasons)


def test_ingest_verifies_binary_and_preserves_review_status(tmp_path):
    from teachersaid.pipeline.image_sources import ingest_image_source

    store, record = _fixture_record(tmp_path)
    assert record.status == "in_review" and record.file.endswith(".jpg")
    store.set_status(record.id, "approved")
    source = record.image_source
    ingest_image_source(store, source, file=record.file, today=TODAY)
    assert store.get(record.id).status == "approved"

    wrong = tmp_path / "wrong.jpg"
    Image.new("RGB", (640, 480), "black").save(wrong, format="JPEG")
    with pytest.raises(ValueError, match="SHA-1"):
        ingest_image_source(store, source, file=wrong, today=TODAY)


def test_tasks_and_answers_are_derived_from_annotations_and_verify_clean(tmp_path):
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.image_sources import build_worksheet
    from teachersaid.pipeline.verify import verify

    _store, record = _fixture_record(tmp_path)
    content, resolution = build_worksheet(record, today=TODAY)
    tasks = [block for block in content.iter_blocks() if block.role == "task"]
    assert [task.answer_key for task in tasks] == [a.answer for a in record.image_source.annotations]
    assert all(task.kind == "source_analysis" for task in tasks)
    asset = content.assets[0]
    assert asset.generator == "file:raster" and asset.role == "source"
    assemble(content, resolution)
    report = verify(content, resolution)
    assert not report.problems, report.problems


def test_same_annotation_engine_routes_kunst_und_gestaltung_to_image_analysis(tmp_path):
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.image_sources import build_worksheet, ingest_image_source
    from teachersaid.pipeline.verify import verify
    from teachersaid.schema.blocks import Serves
    from teachersaid.store.imagesourcestore import ImageSourceStore

    file = tmp_path / "kunst.jpg"
    Image.new("RGB", (640, 480), "white").save(file, format="JPEG")
    sha1 = hashlib.sha1(file.read_bytes()).hexdigest()  # noqa: S324 - file identity
    annotations = [
        annotation.model_copy(update={"dimensions": ["WAH"]})
        for annotation in ISABEY_WIENER_KONGRESS.annotations
    ]
    source = ISABEY_WIENER_KONGRESS.source.model_copy(
        update={"width": 640, "height": 480, "sha1": sha1}
    )
    image = ISABEY_WIENER_KONGRESS.model_copy(
        update={
            "id": "kug-image",
            "image_asset_id": "kug-image-file",
            "subject": "Kunst und Gestaltung",
            "source": source,
            "annotations": annotations,
            "serves": [Serves(competence_id="KUG.US.3.WAH.01", relation="exercises")],
            "related_sachverhalt_id": None,
            "related_text_id": None,
        }
    )
    store = ImageSourceStore(tmp_path / "kunst_store")
    record = ingest_image_source(store, image, file=file, today=TODAY)
    content, resolution = build_worksheet(record, today=TODAY)
    tasks = [block for block in content.iter_blocks() if block.role == "task"]
    assert all(task.kind == "image_analysis" and task.dimensions == ["WAH"] for task in tasks)
    assemble(content, resolution)
    assert not verify(content, resolution).problems


def test_sourced_image_renders_in_student_and_teacher_projections(tmp_path):
    import fitz

    from teachersaid.pipeline.assets import build_asset
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.image_sources import build_worksheet
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide

    _store, record = _fixture_record(tmp_path)
    content, resolution = build_worksheet(record, today=TODAY)
    assemble(content, resolution)
    asset_path = build_asset(content.assets[0], outdir=tmp_path / "assets")
    with Image.open(asset_path) as rendered:
        assert max(rendered.size) <= 1400
    assets = {content.assets[0].id: asset_path}
    student = render_student_sheet(content, tmp_path / "student.pdf", assets)
    teacher = render_teacher_guide(content, tmp_path / "teacher.pdf", assets)
    assert len(fitz.open(student)) >= 1 and len(fitz.open(teacher)) >= 1
    student_text = "".join(page.get_text() for page in fitz.open(student))
    assert "Beschreibung" in student_text and "Rijksmuseum" in student_text


def test_compose_stages_flagship_through_ordinary_gate_two(tmp_path, monkeypatch):
    import teachersaid.config as config
    from teachersaid.pipeline.image_sources import compose_image_source_worksheet
    from teachersaid.store.repository import ReviewStore

    monkeypatch.setattr(config, "RUNS_DIR", tmp_path / "runs")
    image_store, record = _fixture_record(tmp_path)
    item = compose_image_source_worksheet(
        ReviewStore(tmp_path / "review"), image_store, record.id, today=TODAY
    )
    assert item.stage == "content" and item.source == "image_source"
    assert item.error is None and not item.verify_problems
    assert item.artifacts.student_pdf
