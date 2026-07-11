"""Wave B I2: optional Realien backdrops and one worksheet header vignette.

The image binaries are file-backed library artifacts.  These tests use local PIL fixtures only;
pytest never generates an image or reaches the network.
"""

from __future__ import annotations

from datetime import date

import fitz
from PIL import Image as PILImage

from teachersaid.library.realie_bahnhof import BAHNHOF
from teachersaid.library.realie_cafe import CAFE
from teachersaid.library.texts import LORELEY
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.text_tasks import build_worksheet
from teachersaid.rendering.student_sheet import render_student_sheet
from teachersaid.schema.worksheet import WorksheetContent


IN = date(2026, 3, 1)


def _fixture_png(path, *, size=(480, 120)):
    PILImage.new("RGB", size, "#d8c7a7").save(path)
    return path


def _image_count(pdf_path) -> int:
    with fitz.open(pdf_path) as document:
        return sum(len(page.get_images(full=True)) for page in document)


def test_two_curated_realien_carry_stable_optional_backdrop_ids():
    assert BAHNHOF.backdrop_asset == "img-realie-bahnhof-backdrop"
    assert CAFE.backdrop_asset == "img-realie-cafe-backdrop"

    content, resolution = build_worksheet(BAHNHOF, today=IN)
    assemble(content, resolution)
    material = next(
        block for block in content.iter_blocks()
        if getattr(block, "kind", None) == "source_text"
    )
    assert material.numbered is False
    assert material.backdrop_asset_ref == BAHNHOF.backdrop_asset


def test_material_card_embeds_resolved_backdrop_but_keeps_live_text(tmp_path):
    content, resolution = build_worksheet(BAHNHOF, today=IN)
    assemble(content, resolution)
    backdrop = _fixture_png(tmp_path / "station.png")
    pdf = render_student_sheet(
        content,
        tmp_path / "with-backdrop.pdf",
        {BAHNHOF.backdrop_asset: backdrop},
    )
    assert _image_count(pdf) == 1
    with fitz.open(pdf) as document:
        page_text = "\n".join(page.get_text() for page in document)
    assert "08:14" in page_text and "Platform 3" in page_text


def test_missing_optional_backdrop_degrades_to_plain_material_card(tmp_path):
    content, resolution = build_worksheet(BAHNHOF, today=IN)
    assemble(content, resolution)
    pdf = render_student_sheet(content, tmp_path / "without-backdrop.pdf", {})
    assert _image_count(pdf) == 0


def test_one_explicitly_selected_theme_vignette_renders_in_title_zone(tmp_path):
    content, resolution = build_worksheet(
        LORELEY,
        today=IN,
        theme_asset="img-theme-literatur",
    )
    assemble(content, resolution)
    vignette = _fixture_png(tmp_path / "theme.png", size=(180, 120))
    pdf = render_student_sheet(
        content,
        tmp_path / "with-theme.pdf",
        {"img-theme-literatur": vignette},
    )
    assert content.theme_asset == "img-theme-literatur"
    assert _image_count(pdf) == 1


def test_theme_and_backdrop_refs_roundtrip_and_missing_theme_is_safe(tmp_path):
    content, resolution = build_worksheet(
        BAHNHOF,
        today=IN,
        theme_asset="img-theme-travel",
    )
    assemble(content, resolution)
    reloaded = WorksheetContent.model_validate_json(content.model_dump_json())
    material = next(
        block for block in reloaded.iter_blocks()
        if getattr(block, "kind", None) == "source_text"
    )
    assert reloaded.theme_asset == "img-theme-travel"
    assert material.backdrop_asset_ref == "img-realie-bahnhof-backdrop"

    # File-backed images are optional at render time (e.g. before Drive sync or SME approval).
    pdf = render_student_sheet(reloaded, tmp_path / "missing-both.pdf", {})
    assert _image_count(pdf) == 0

