"""Phase 0 (Oberstufe enabler): stage-aware grounding + semester/Kompetenzmodul resolution.

Locks the Oberstufe catalog wiring: the Klasse drives the stage, the per-subject models mirror
the Lehrplan (incl. Chemie's non-W/E/S triad), competences carry semester/kompetenzmodul/kind,
the Kompetenzmodul filter narrows correctly, Oberstufe-only subjects resolve, and the Unterstufe
path is unchanged.
"""

from __future__ import annotations

from datetime import date

from teachersaid.grounding import lehrplan_store as store
from teachersaid.pipeline import resolve as R
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import make_variants
from teachersaid.pipeline.verify import verify
from teachersaid.library.templates import PARAM_TEMPLATES, find_template, variant_worksheet
from teachersaid.schema.worksheet import BundleRequest

IN_WINDOW = date(2026, 3, 1)  # inside the Fassung window (no window warning)

OS_MATH = [t for t in PARAM_TEMPLATES if t.id.startswith("mat-os-")]


def test_stufe_for_klasse():
    assert [store.stufe_for_klasse(k) for k in (1, 4, 5, 8)] == [
        "Unterstufe", "Unterstufe", "Oberstufe", "Oberstufe"
    ]


def test_chemie_oberstufe_model_is_not_wes():
    """The load-bearing trap: Oberstufe Chemie uses Wissen organisieren / Erkenntnisse
    gewinnen / Konsequenzen ziehen — NOT the W/E/S of Physik/Biologie."""
    m = store.get_subject_model("Chemie", "Oberstufe")
    assert m is not None and m.stufe == "Oberstufe"
    assert m.dimension_ids() == {"WO", "EG", "KZ"}
    # ...while Oberstufe Physik/Biologie keep W/E/S
    assert store.get_subject_model("Physik", "Oberstufe").dimension_ids() == {"W", "E", "S"}
    assert store.get_subject_model("Biologie", "Oberstufe").dimension_ids() == {"W", "E", "S"}


def test_fremdsprache_modality_split():
    m = store.get_subject_model("Lebende Fremdsprache", "Oberstufe")
    by_id = {d.id: d.modality.value for d in m.dimensions}
    assert by_id["HOR"] == "oral"      # Hören (audio→oral)
    assert by_id["LES"] == "printable"
    assert by_id["SCH"] == "printable"


def test_oberstufe_only_subject_resolves_in_sek_ii():
    """Ethik is Oberstufe-only: a gap at Kl. 4, but resolves at Kl. 7."""
    gap = R.resolve(BundleRequest(subject="Ethik", klasse=4, topic_raw="Glück"), today=IN_WINDOW)
    assert gap.grade_check is False

    res = R.resolve_grade("Ethik", 7, today=IN_WINDOW)
    assert res.grade_check is True
    assert res.competences
    assert any(c.kind == "descriptor" for c in res.competences)


def test_oberstufe_competences_carry_semester_and_kind():
    res = R.resolve_grade("Mathematik", 7, today=IN_WINDOW)
    assert res.grade_check is True
    lehr = [c for c in res.competences if c.kind == "lehrstoff"]
    desc = [c for c in res.competences if c.kind == "descriptor"]
    assert lehr and desc
    # every grade-7 Lehrstoff competence sits in a Kompetenzmodul with a semester
    assert all(c.kompetenzmodul in (5, 6) and c.semester for c in lehr)
    assert all(c.id.startswith("MAT.OS.7.") for c in lehr)
    assert all(c.id.startswith("MAT.OS.x.") for c in desc)  # grade-independent descriptors


def test_kompetenzmodul_filter_narrows_but_keeps_descriptors():
    full = R.resolve_grade("Mathematik", 7, today=IN_WINDOW)
    km5 = R.resolve_kompetenzmodul("Mathematik", 7, 5, today=IN_WINDOW)
    full_lehr = [c for c in full.competences if c.kind == "lehrstoff"]
    km5_lehr = [c for c in km5.competences if c.kind == "lehrstoff"]
    assert 0 < len(km5_lehr) < len(full_lehr)
    assert all(c.kompetenzmodul == 5 for c in km5_lehr)
    # cross-cutting descriptors are retained under the narrowed view
    assert [c.id for c in km5.competences if c.kind == "descriptor"] == \
           [c.id for c in full.competences if c.kind == "descriptor"]


def test_biologie_descriptors_recover_wes_dimension():
    res = R.resolve_grade("Biologie", 7, today=IN_WINDOW)
    desc = [c for c in res.competences if c.kind == "descriptor"]
    assert desc
    tagged = [c for c in desc if c.dimensions]
    assert tagged and all(set(c.dimensions) <= {"W", "E", "S"} for c in tagged)
    assert any("W" in c.dimensions for c in tagged)


def test_physik_kernphysik_resolves_in_8th_grade():
    res = R.resolve_kompetenzbereich("Physik", 8, "Kernphysik", today=IN_WINDOW)
    assert res.grade_check is True
    assert res.competences
    assert all(c.klasse == 8 for c in res.competences if c.kind == "lehrstoff")


def test_unterstufe_path_unchanged():
    """Klasse 4 stays Unterstufe: Strahlung resolves, competences are .US. with kind=None."""
    res = R.resolve(
        BundleRequest(subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität"),
        today=IN_WINDOW,
    )
    assert res.grade_check is True and res.competences
    assert all(c.id.startswith("PHY.US.") and c.kind is None for c in res.competences)


# --- Phase 1: the Oberstufe Mathematik parametric pack -------------------------------

def test_oberstufe_maths_pack_covers_all_inhaltsbereiche():
    ids = {t.id for t in OS_MATH}
    assert ids == {
        "mat-os-kurvendiskussion", "mat-os-integral", "mat-os-lgs2",
        "mat-os-lgs3", "mat-os-binomial", "mat-os-skalarprodukt",
    }
    # all four Oberstufe MAT content areas are represented
    assert {t.content_area for t in OS_MATH} == {
        "Analysis", "Algebra und Geometrie", "Wahrscheinlichkeit und Statistik",
    }


def test_oberstufe_maths_templates_build_assemble_verify():
    """Every Oberstufe MAT template → N correct-by-construction variants that assemble +
    verify clean, with the Nachweis binding the served Oberstufe competence."""
    for t in OS_MATH:
        content, res = variant_worksheet(t, n=3, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (t.id, rep.problems)          # no problems
        assert content.meta.stufe == "Oberstufe"
        blocks = content.sections[0].blocks
        assert len(blocks) == 3
        assert all(b.solution_steps and b.answer_key for b in blocks)
        # block dimensions are valid against the Oberstufe MAT model (DM/FO/ID/KA)
        dim_ids = content.subject_model.dimension_ids()
        assert all(set(b.dimensions) <= dim_ids for b in blocks)
        # the derived Nachweis marks the served competence covered (the trust feature)
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (t.id, served, "not covered in Nachweis")


def test_parametric_variants_deterministic_and_distinct():
    t = find_template("mat-os-kurvendiskussion")
    a = make_variants(t, 4, seed0=1)
    b = make_variants(t, 4, seed0=1)
    assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b]   # deterministic per seed
    assert len({str(x.prompt) for x in a}) >= 3                       # variants actually differ
    assert all(x.answer_key and x.solution_steps for x in a)


def test_oberstufe_maths_inline_math_renders(tmp_path):
    """Render exercises matplotlib mathtext on every LaTeX run — guards the mathtext-subset
    traps that assemble/verify can't catch (\\leq not \\le; \\binom for vectors; NO
    \\begin{pmatrix}/\\begin{cases})."""
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    for t in OS_MATH:
        content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
        content = assemble(content, res)
        for render in (render_student_sheet, render_teacher_guide):
            out = render(content, tmp_path / f"{t.id}_{render.__name__}.pdf")
            assert out.exists() and out.stat().st_size > 1000, (t.id, render.__name__)
