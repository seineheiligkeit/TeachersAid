"""M3 verification: assets build, all three projections render, rasters produced."""

from __future__ import annotations

from datetime import date

import fitz  # PyMuPDF
import pytest

from teachersaid.demo import strahlung
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.resolve import resolve
from teachersaid.rendering.homework import render_homework
from teachersaid.rendering.qa_raster import rasterise
from teachersaid.rendering.student_sheet import render_student_sheet
from teachersaid.rendering.teacher_guide import render_teacher_guide

IN_WINDOW = date(2026, 3, 1)


@pytest.fixture
def built(tmp_path):
    content = strahlung.build_content()
    res = resolve(strahlung.build_request(), today=IN_WINDOW)
    assemble(content, res)
    assets = {}
    for a in content.assets:
        assets[a.id] = build_asset(a, outdir=tmp_path / "assets")
    return content, assets, tmp_path


def test_em_spectrum_asset_builds(built):
    _, assets, _ = built
    p = assets["em_spectrum"]
    assert p.exists() and p.stat().st_size > 1000


def test_all_three_projections_render_and_rasterise(built):
    content, assets, tmp = built
    outputs = {
        "student": render_student_sheet(content, tmp / "student.pdf", assets),
        "teacher": render_teacher_guide(content, tmp / "teacher.pdf", assets),
        "homework": render_homework(content, tmp / "homework.pdf", assets),
    }
    for name, pdf in outputs.items():
        assert pdf.exists() and pdf.stat().st_size > 2000, name
        with fitz.open(pdf) as doc:
            assert doc.page_count >= 1
            text = "".join(page.get_text() for page in doc)
        assert "Strahlung und Radioaktivität" in text, name
        pages = rasterise(pdf, out_dir=tmp / "raster")
        assert pages and all(p.exists() for p in pages), name


def test_student_hides_keys_teacher_shows_them(built):
    content, assets, tmp = built
    s = render_student_sheet(content, tmp / "s.pdf", assets)
    t = render_teacher_guide(content, tmp / "t.pdf", assets)

    def text_of(pdf):
        with fitz.open(pdf) as doc:
            return "".join(p.get_text() for p in doc)

    s_text, t_text = text_of(s), text_of(t)
    # answer key text appears only in the teacher projection
    assert "UV schädigt Zellen" in t_text
    assert "UV schädigt Zellen" not in s_text
    # the Nachweis + gap appears only in the teacher guide
    assert "LÜCKE" in t_text or "Nachweis" in t_text
    assert "PHY.US.4.STR.01" in t_text


def test_projection_audience_split(built):
    """Student-facing vs teacher-facing: the Fassung stamp and the teacher 'rough
    guide' layer (talking points / extensions) belong only on the teacher copy."""
    content, assets, tmp = built

    def text_of(pdf):
        with fitz.open(pdf) as doc:
            return "".join(p.get_text() for p in doc)

    s_text = text_of(render_student_sheet(content, tmp / "s2.pdf", assets))
    t_text = text_of(render_teacher_guide(content, tmp / "t2.pdf", assets))

    assert "DokNr" in t_text and "DokNr" not in s_text          # Fassung: teacher-only
    assert "Gesprächsanker" in t_text and "Gesprächsanker" not in s_text  # talking points
    assert "Erweiterung" in t_text and "Erweiterung" not in s_text        # extensions


def test_teacher_guide_drops_the_write_space(built):
    """The teacher knows the topic — the guide omits the student's answer space
    (ruled lines / box), which renders as a ReportLab Table."""
    from reportlab.platypus import Table

    from teachersaid.rendering import reportlab_base as rb
    from teachersaid.rendering.blocks_to_flowables import block_flowables

    content, _, _ = built
    S = rb.styles()
    # an open-response task: write-space comes purely from `response` (no payload table)
    task = next(b for b in content.iter_blocks()
                if b.role == "task" and b.payload is None
                and b.response.mode in ("lines", "box"))

    def tables(projection):
        flat, stack = [], list(block_flowables(task, projection, S, 400, {}, number=1))
        while stack:
            f = stack.pop()
            inner = getattr(f, "_content", None)
            stack.extend(inner) if inner else flat.append(f)
        return [f for f in flat if isinstance(f, Table)]

    assert tables("student"), "student should get ruled answer lines / a box"
    assert not tables("teacher"), "teacher guide should omit the write-in space"


def test_intentionally_flawed_guard():
    from teachersaid.schema.assets import Asset, IntentionallyFlawed

    bad = Asset(
        id="x",
        role="figure",
        generator="matplotlib:em_spectrum",
        intentionally_flawed=IntentionallyFlawed(what="axis truncated"),
    )
    with pytest.raises(ValueError):
        build_asset(bad)
