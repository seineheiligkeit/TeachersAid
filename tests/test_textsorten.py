"""SRDP Deutsch Textsorten + Schreibhandlungen grounding (the German genre layer)."""
from __future__ import annotations

from teachersaid.grounding import textsorten as ts
from teachersaid.grounding import operators as ops


def test_catalog_complete():
    assert set(ts.TEXTSORTEN) == {
        "eroerterung", "kommentar", "leserbrief", "meinungsrede",
        "textanalyse", "textinterpretation", "zusammenfassung"}
    assert set(ts.SCHREIBHANDLUNGEN) == {
        "deskription", "narration", "explikation", "argumentation",
        "rekapitulation", "evaluation"}


def test_textsorten_well_formed():
    for t in ts.TEXTSORTEN.values():
        assert t.schreibhandlungen, f"{t.id} has no Schreibhandlungen"
        # every referenced Schreibhandlung is a real one
        assert all(s in ts.SCHREIBHANDLUNGEN for s in t.schreibhandlungen)
        assert t.umfang and all(lo < hi for lo, hi in t.umfang)
        assert t.textbasis in ("literarisch", "nicht-fiktional", "pragmatisch")
        assert t.scope in ("kurz", "lang", "variabel")


def test_faithful_to_katalog():
    # the two text-bound Textsorten carry the right basis + writing-acts
    assert ts.TEXTSORTEN["textinterpretation"].textbasis == "literarisch"
    assert ts.TEXTSORTEN["textanalyse"].textbasis == "nicht-fiktional"
    # Zusammenfassung is pure compression — no Argumentation, no Evaluation
    z = ts.TEXTSORTEN["zusammenfassung"].schreibhandlungen
    assert "rekapitulation" in z and "argumentation" not in z and "evaluation" not in z
    # Erörterung / Kommentar / Leserbrief draw on all six
    assert len(ts.TEXTSORTEN["eroerterung"].schreibhandlungen) == 6
    # word-count: Textinterpretation long-only, Leserbrief short-only
    assert ts.TEXTSORTEN["textinterpretation"].umfang == ((540, 660),)
    assert ts.TEXTSORTEN["leserbrief"].umfang == ((270, 330),)


def test_resolution_and_helpers():
    assert ts.get_textsorte("Erörterung") is ts.TEXTSORTEN["eroerterung"]
    assert ts.get_textsorte("kommentar").name == "Kommentar"
    assert ts.get_textsorte("nonsense") is None
    names = {s.name for s in ts.schreibhandlungen_for("Meinungsrede")}
    assert "Argumentation" in names and "Evaluation" not in names
    assert ts.TEXTSORTEN["textinterpretation"] in ts.by_scope("lang")


def test_brief_renders():
    brief = ts.format_textsorte_brief("Erörterung")
    assert "Erörterung" in brief and "Argumentation" in brief and "540–660" in brief


def test_crosswalk_targets_are_real_deutsch_operators():
    """The Schreibhandlung→operator cross-walk must point at actual DEUTSCH catalog
    operators — ties the genre layer to the operator grounding."""
    catalog = {o.forms for o in ops.DEUTSCH}
    for sh, forms in ts.SCHREIBHANDLUNG_OPERATORS.items():
        assert sh in ts.SCHREIBHANDLUNGEN
        for f in forms:
            assert f in catalog, f"{f!r} (for {sh}) is not a DEUTSCH operator"


# --- the genre-scaffold layer: new grounding fields + the derivation pipeline --------------

import fitz  # PyMuPDF
import pytest

from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.textsorte_scaffold import build_worksheet
from teachersaid.pipeline.verify import verify
from teachersaid.rendering.student_sheet import render_student_sheet
from teachersaid.rendering.teacher_guide import render_teacher_guide

# The top-3 SRDP Textsorten by archive frequency, at their honest grades.
TOP3 = [("zusammenfassung", 3), ("kommentar", 4), ("textinterpretation", 4)]


def test_new_grounding_fields_complete():
    """struktur (ordered Bauteil/Funktion), typical_operators (verbatim DEUTSCH forms),
    sprachregister, artikel and source note are present + well-formed for every Textsorte."""
    ops_forms = {o.forms for o in ops.DEUTSCH}
    for t in ts.TEXTSORTEN.values():
        assert t.struktur and all(len(x) == 2 and x[0] and x[1] for x in t.struktur), t.id
        assert t.typical_operators, t.id
        for f in t.typical_operators:                     # select-never-author: real operators
            assert f in ops_forms, f"{f!r} (for {t.id}) is not a DEUTSCH operator"
        assert t.sprachregister.strip(), t.id
        assert t.artikel in ("eine", "einen"), t.id
        assert t.quelle and "Datenquelle" in t.quelle, t.id


def test_struktur_teile_helper():
    assert ts.struktur_teile("Kommentar") == ["Titel", "Einleitung", "Hauptteil", "Schluss"]
    assert ts.struktur_teile("nonsense") == []


def test_brief_includes_aufbau_and_operators():
    brief = ts.format_textsorte_brief("Kommentar")
    assert "Aufbau:" in brief and "Titel" in brief
    assert "kommentieren / Stellung nehmen" in brief  # a typical operator, verbatim
    assert "Sprachregister:" in brief


@pytest.mark.parametrize("tsid,kl", TOP3)
def test_build_assemble_verify_clean(tsid, kl):
    """Each scaffold builds, assembles and verifies clean — no problems, no warnings EXCEPT
    the one expected readability advisory: the capstone (tx.t3) is deliberately Matura-FORMAT
    task language (operator heads, SRDP register) — that register IS the genre being taught,
    so the Wiener-Sachtextformel may rate it above grade. The learn-text (tx.i1) and every
    other block must be grade-readable — any warning there fails."""
    content, res = build_worksheet(tsid, kl)
    assemble(content, res)
    rep = verify(content, res)
    assert rep.ok, rep.problems
    unexpected = [w for w in rep.warnings
                  if not w.startswith("tx.t3: Lesbarkeit (Wiener Sachtextformel)")]
    assert not unexpected, unexpected
    tasks = [b for b in content.iter_blocks() if b.role == "task"]
    # verstehen → planen → verfassen, a real Anforderungs-spread
    assert [t.kind for t in tasks] == ["matching", "table_fill", "text_production"]
    assert {t.cognitive_level for t in tasks} == {"understand", "apply", "create"}
    # serves anchor to REAL, resolving DEU Schreiben competences (honest 3./4. Kl.)
    valid = {c.id for c in res.competences}
    served = {s.competence_id for t in tasks for s in t.serves}
    assert served and served <= valid
    assert all(".SCH." in cid for cid in served), served
    # the capstone exercises the Schreiben competence; the scaffolds build toward it
    cap = tasks[-1]
    assert cap.kind == "text_production" and cap.dimensions == ["SCH"]
    assert any(s.relation == "exercises" for s in cap.serves)


@pytest.mark.parametrize("tsid,kl", TOP3)
def test_capstone_is_matura_shaped(tsid, kl):
    """The capstone is an operator-headed Arbeitsauftrag with the Wortanzahl band + a box."""
    content, _ = build_worksheet(tsid, kl)
    tsrec = ts.get_textsorte(tsid)
    cap = [b for b in content.iter_blocks() if getattr(b, "kind", None) == "text_production"][0]
    prompt = cap.prompt if isinstance(cap.prompt, str) else "".join(r.text for r in cap.prompt)
    assert f"Verfasse {tsrec.artikel} {tsrec.name}" in prompt
    lo, hi = tsrec.umfang[0]
    assert f"{lo}–{hi} Wörter" in prompt          # "270–330 Wörter"
    assert cap.response.mode == "box"


@pytest.mark.parametrize("tsid,kl", TOP3)
def test_capstone_rubric_derives_from_curated_grounding(tsid, kl):
    """The load-bearing property: the capstone rubric is DERIVED from the curated
    Schreibhandlungen + Struktur (the Erwartungshorizont from grounding, not invented)."""
    from teachersaid.pipeline.textsorte_scaffold import _LEIT_SCHREIBHANDLUNGEN

    content, _ = build_worksheet(tsid, kl)
    tsrec = ts.get_textsorte(tsid)
    cap = [b for b in content.iter_blocks() if getattr(b, "kind", None) == "text_production"][0]
    crit_text = " || ".join(c.criterion for c in cap.rubric)
    # every leitende Schreibhandlung shows up as a rubric criterion (by its grounded name)
    leit = _LEIT_SCHREIBHANDLUNGEN[tsid]
    assert leit
    for sh in leit:
        assert ts.SCHREIBHANDLUNGEN[sh].name in crit_text, sh
    # the Struktur (Aufbau) is a criterion listing every Bauteil
    for teil in ts.struktur_teile(tsid):
        assert teil in crit_text, teil
    # the Wortanzahl band is a criterion
    lo, hi = tsrec.umfang[0]
    assert f"{lo}–{hi}" in crit_text
    # every criterion uses the three-band SRDP scale
    assert cap.rubric and all(
        c.levels == ["nicht erreicht", "teilweise erreicht", "erreicht"] for c in cap.rubric)


@pytest.mark.parametrize("tsid,kl", TOP3)
def test_projections_render_and_split_audience(tsid, kl, tmp_path):
    """All projections render; the rubric is teacher-only (the audience split holds)."""
    content, res = build_worksheet(tsid, kl)
    assemble(content, res)
    sp = render_student_sheet(content, tmp_path / "s.pdf", {})
    tp = render_teacher_guide(content, tmp_path / "t.pdf", {})
    stext = "".join(p.get_text() for p in fitz.open(sp))
    ttext = "".join(p.get_text() for p in fitz.open(tp))
    lo, hi = ts.get_textsorte(tsid).umfang[0]
    assert str(lo) in stext and str(hi) in stext          # Wortanzahl band on the student sheet
    assert "Kriterium" not in stext                       # rubric hidden from students
    assert "Kriterium" in ttext                           # rubric shown to the teacher


def test_seed_textsorten_stages_items(tmp_path):
    """seed_textsorten mirrors seed_history: three pending, error-free content items."""
    from teachersaid.library import seed_textsorten
    from teachersaid.store.repository import ReviewStore

    items = seed_textsorten(ReviewStore(str(tmp_path)))
    assert len(items) == 3
    assert all(it.status == "pending" and not it.error for it in items), \
        [(it.id, it.error) for it in items]
    assert all(not it.verify_problems for it in items)
    assert {it.title for it in items} == {
        "Zusammenfassung schreiben", "Kommentar schreiben", "Textinterpretation schreiben"}


def test_unknown_textsorte_raises():
    with pytest.raises(KeyError):
        build_worksheet("nonexistent", 4)
