"""M2 verification: deterministic resolution + honest gaps."""

from __future__ import annotations

from datetime import date

from teachersaid.grounding import lehrplan_store as store
from teachersaid.pipeline.resolve import resolve
from teachersaid.schema.worksheet import BundleRequest

# A date inside the Fassung window so the window-warning doesn't fire.
IN_WINDOW = date(2026, 3, 1)


def test_strahlung_resolves_with_grade_check():
    req = BundleRequest(
        subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität"
    )
    res = resolve(req, today=IN_WINDOW)
    assert res.grade_check is True
    ids = {c.id for c in res.competences}
    assert ids == {
        "PHY.US.4.STR.01",
        "PHY.US.4.STR.02",
        "PHY.US.4.STR.03",
        "PHY.US.4.STR.04",
    }
    assert "Strahlung und Radioaktivität" in res.matched_kompetenzbereiche
    # verbatim text + ÜT tag preserved
    str02 = next(c for c in res.competences if c.id == "PHY.US.4.STR.02")
    assert "Interaktion" in str02.text  # verbatim from the Fassung (catalog)
    assert 11 in str02.uebergreifende_themen


def test_out_of_catalogue_subject_reports_gap():
    # Ethik is Oberstufe-only in this Fassung — not in the Unterstufe catalog.
    req = BundleRequest(subject="Ethik", klasse=4, topic_raw="Tugend und Glück")
    res = resolve(req, today=IN_WINDOW)
    assert res.grade_check is False
    assert res.competences == []
    assert any("nicht hinterlegt" in n for n in res.notes)


def test_subject_known_but_grade_uncurated_reports_gap():
    # Physik runs Kl. 2–4; Kl. 1 has no curated competences.
    req = BundleRequest(subject="Physik", klasse=1, topic_raw="Energie")
    res = resolve(req, today=IN_WINDOW)
    assert res.competences == []
    assert any("keine Kompetenzen" in n for n in res.notes)


def test_fassung_window_warning_outside_window():
    req = BundleRequest(
        subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität"
    )
    res = resolve(req, today=date(2026, 10, 1))  # after valid_to
    assert any("Fassungsfensters" in n for n in res.notes)


def test_science_model_sharing():
    # Chemie/Biologie reuse the Physik (Naturwissenschaften) W/E/S model.
    chem = store.get_subject_model("Chemie")
    assert chem is not None
    assert {d.id for d in chem.dimensions} == {"W", "E", "S"}
