"""M6 verification: the three worked examples render and exercise v0.4 deltas."""

from __future__ import annotations

import fitz  # PyMuPDF
import pytest

from teachersaid.demo import worked_examples as we
from teachersaid.pipeline.assets import build_asset
from teachersaid.rendering.student_sheet import render_student_sheet
from teachersaid.rendering.teacher_guide import render_teacher_guide


def _assets(content, outdir):
    return {a.id: build_asset(a, outdir=outdir) for a in content.assets if a.generator}


def _text(pdf):
    with fitz.open(pdf) as doc:
        return "".join(p.get_text() for p in doc)


def test_english_oral_task_dropped_from_student(tmp_path):
    c = we.build_english()
    a = _assets(c, tmp_path)
    s = _text(render_student_sheet(c, tmp_path / "s.pdf", a))
    t = _text(render_teacher_guide(c, tmp_path / "t.pdf", a))
    # the printable listening task is on both
    assert "TWO reasons" in s and "TWO reasons" in t
    # the ORAL speaking task is teacher-only (absent from the printed student sheet)
    assert "summarise the speech" in t
    assert "summarise the speech" not in s
    # audio asset is sourced, not machine-generatable
    audio = next(x for x in c.assets if x.medium == "audio")
    assert audio.machine_generatable is False and audio.provenance is not None


def test_geschoente_kurve_cross_curricular_and_flawed(tmp_path):
    c = we.build_geschoente_kurve()
    # B5: two subject models cited
    assert [m.ref for m in c.meta.subject_models] == ["Physik", "Mathematik"]
    # the intentionally-flawed asset exists and is built by a flaw-preserving generator
    flawed = next(x for x in c.assets if x.intentionally_flawed)
    assert flawed.generator == "matplotlib:truncated_axis"
    a = _assets(c, tmp_path)
    assert flawed.id in a and a[flawed.id].exists()  # rendered wrong-on-purpose, not fixed
    s = _text(render_student_sheet(c, tmp_path / "s.pdf", a))
    t = _text(render_teacher_guide(c, tmp_path / "t.pdf", a))
    # the cross-curricular task cites both competence sources (teacher view)
    assert "PHY.US.4.STR.02" in t and "MA.US.4.DATEN.x" in t
    # the load-bearing watch-out (don't leave as climate deniers) is teacher-only
    assert "Klimaskeptiker" in t and "Klimaskeptiker" not in s


def test_math_unfair_game_rubric_and_artifact(tmp_path):
    c = we.build_math_unfair_game()
    task = c.sections[0].blocks[0]
    assert task.response.mode == "artifact"
    assert len(task.rubric) == 2
    assert task.cognitive_level == "create"
    t = _text(render_teacher_guide(c, tmp_path / "t.pdf", {}))
    # rubric criteria surface in the teacher guide
    assert "Regeln klar" in t and "Begründung mit Wahrscheinlichkeit" in t


def test_all_three_render_without_error(tmp_path):
    for name, build in we.ALL.items():
        c = build()
        a = _assets(c, tmp_path / name)
        for proj, fn in (("s", render_student_sheet), ("t", render_teacher_guide)):
            pdf = fn(c, tmp_path / f"{name}_{proj}.pdf", a)
            assert pdf.exists() and pdf.stat().st_size > 1500, name
