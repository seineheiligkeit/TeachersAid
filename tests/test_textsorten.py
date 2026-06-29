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
