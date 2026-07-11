"""The two Sternkarten-Engine worksheets — the competence-anchored Mondphasen sheet and
the first real Horizont flagship (Sternenhimmel über Wien). Locks them the way
test_gpb_wiener_kongress locks the History flagship: build → resolve → assemble → verify
CLEAN, honest Nachweis, the masking invariant, and a clean seed into the review store."""
from __future__ import annotations

from datetime import date

import fitz
import pytest

from teachersaid.library import phy_mondphasen as mp
from teachersaid.library import phy_sternenhimmel as sk
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.resolve import resolve, resolve_kompetenzbereich
from teachersaid.pipeline.verify import verify
from teachersaid.rendering.teacher_guide import render_teacher_guide
from teachersaid.schema.enums import AnchorMode

TODAY = date(2026, 3, 1)


# --- the competence-anchored Mondphasen sheet (PHY.US.2.SEH.04) --------------
def _mondphasen():
    c = mp.build_content()
    res = resolve_kompetenzbereich(mp.SUBJECT, mp.KLASSE, mp.KOMPETENZBEREICH, today=TODAY)
    assemble(c, res)
    return c, res


def test_mondphasen_verifies_clean_on_a_real_competence():
    c, res = _mondphasen()
    rep = verify(c, res)
    assert rep.problems == [], rep.problems
    hard = [w for w in rep.warnings if "Lesbarkeit" not in w]        # readability is advisory
    assert hard == [], hard
    assert c.anchor_mode == AnchorMode.COMPETENCE
    # it lands on the verbatim moon/day-night/seasons competence
    served = {s.competence_id for b in c.iter_blocks() for s in getattr(b, "serves", [])}
    assert "PHY.US.2.SEH.04" in served


def test_mondphasen_nachweis_covers_seh04_and_surfaces_honest_gaps():
    c, _ = _mondphasen()
    n = c.nachweis
    assert n.anchor_mode == AnchorMode.COMPETENCE
    covered = {cc.competence_id for cc in n.competence_coverage if cc.covered}
    assert {"PHY.US.2.SEH.03", "PHY.US.2.SEH.04"} <= covered
    # the sibling „Sehen und Hören" competences are honestly left as gaps (not faked)
    gap_ids = {g.split(" — ")[0] for g in n.gaps}
    assert {"PHY.US.2.SEH.01", "PHY.US.2.SEH.02", "PHY.US.2.SEH.05"} <= gap_ids


def test_mondphasen_task_figures_are_masked_and_computed():
    c, _ = _mondphasen()
    assets = {a.id: a for a in c.assets}
    # every phase figure is the COMPUTED moon recipe
    assert all(a.generator == "matplotlib:moon_phase" for a in c.assets)
    # the ordering-task figures A/B/C hide their phase name (show_label False)
    for aid in ("mp-a", "mp-b", "mp-c", "mp-t1"):
        assert assets[aid].spec["show_label"] is False
    # the intro example is allowed to name the phase
    assert assets["mp-beispiel"].spec["show_label"] is True


def test_mondphasen_renders(tmp_path):
    c, _ = _mondphasen()
    for a in c.assets:
        assert build_asset(a, outdir=tmp_path).exists()


# --- the Horizont flagship (Sternenhimmel über Wien) ------------------------
def _sternenhimmel():
    c = sk.build_content()
    res = resolve(sk.build_request(), today=TODAY)
    assemble(c, res)
    return c, res


def test_sternenhimmel_is_horizont_and_verifies_clean():
    c, res = _sternenhimmel()
    assert res.grade_check is True and res.competences == []       # horizont: zero competences
    rep = verify(c, res)
    assert rep.problems == [], rep.problems
    hard = [w for w in rep.warnings if "Lesbarkeit" not in w]
    assert hard == [], hard
    assert c.anchor_mode == AnchorMode.HORIZONT


def test_sternenhimmel_claims_no_competence_anywhere():
    c, _ = _sternenhimmel()
    # the defining Horizont property: not a single task may carry a `serves` hook
    assert all(b.serves == [] for b in c.iter_blocks() if getattr(b, "serves", None) is not None)
    n = c.nachweis
    assert n.anchor_mode == AnchorMode.HORIZONT
    assert n.competence_coverage == [] and n.gaps == []
    assert "kein Lehrplan-Kompetenzbezug" in n.statement


def test_sternenhimmel_riddle_masks_the_constellation_name():
    c, _ = _sternenhimmel()
    riddle = next(a for a in c.assets if a.id == "sky-raetsel")
    # the riddle chart highlights a constellation but must not print its name
    assert riddle.spec.get("highlight") == "UMa"
    assert riddle.spec.get("show_constellation_labels") in (None, False)


def test_sternenhimmel_teacher_pdf_renders_horizont_nachweis(tmp_path):
    c, _ = _sternenhimmel()
    assets = {a.id: build_asset(a, outdir=tmp_path / "assets") for a in c.assets}
    pdf = render_teacher_guide(c, tmp_path / "teacher.pdf", assets)
    text = "\n".join(page.get_text() for page in fitz.open(pdf))
    assert "Verankerungsmodus: Horizont" in text
    assert "kein Lehrplan-Kompetenzbezug" in text
    assert "LÜCKE" not in text                                      # horizont makes no gap claim


# --- the seed path ----------------------------------------------------------
def test_seed_astronomy_stages_both_clean(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.library import seed_astronomy
    from teachersaid.store.repository import ReviewStore

    items = seed_astronomy(ReviewStore(tmp_path / "store"), today=TODAY)
    assert len(items) == 2
    for it in items:
        assert it.error is None, it.error
        assert it.verify_problems == [], it.verify_problems
        assert it.status == "pending"
        assert it.artifacts and it.artifacts.student_pdf     # rendered for the Vorschau
    modes = {it.content.anchor_mode for it in items}
    assert modes == {AnchorMode.COMPETENCE, AnchorMode.HORIZONT}
