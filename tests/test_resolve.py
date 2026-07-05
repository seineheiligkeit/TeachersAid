"""M2 verification: deterministic resolution + honest gaps."""

from __future__ import annotations

from datetime import date

from teachersaid.grounding import lehrplan_store as store
from teachersaid.pipeline.resolve import resolve, resolve_grade
from teachersaid.schema.worksheet import BundleRequest
from teachersaid.stats import coverage_map

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


def test_che2_reachable_by_distinct_display_name():
    """Two Unterstufe subjects are both headed 'CHEMIE' in the RIS source (CHE = AHS
    4. Kl.; CHE2 = Wirtschaftskundliches RG, 3.–4. Kl.). A curated distinct display name
    makes CHE2 routable by subject-name end-to-end, WITHOUT regressing plain 'Chemie' → CHE."""
    dist = store._DISPLAY_NAME_OVERRIDES[("Unterstufe", "CHE2")]
    assert dist != "CHEMIE"

    # plain name still routes to CHE (no regression); the distinct name routes to CHE2
    assert store._code_for("Chemie", "Unterstufe") == "CHE"
    assert store._code_for("CHEMIE", "Unterstufe") == "CHE"
    assert store._code_for(dist, "Unterstufe") == "CHE2"
    assert store._code_for("CHE2", "Unterstufe") == "CHE2"  # the code routes directly too

    # the distinct name is surfaced (resolve's gap note, briefs, stats) and the collision
    # is resolved rather than duplicated
    subjects = store.list_subjects("Unterstufe")
    assert dist in subjects
    assert subjects.count("CHEMIE") == 1

    # CHE2 carries the science W/E/S model; its own competences resolve for BOTH its grades
    model = store.get_subject_model(dist, "Unterstufe")
    assert {d.id for d in model.dimensions} == {"W", "E", "S"}
    for klasse in (3, 4):
        res = resolve_grade(dist, klasse, today=IN_WINDOW)
        assert res.grade_check is True
        assert res.competences and all(c.id.startswith("CHE2.") for c in res.competences)

    # the pre-fix break, preserved as a witness: CHE has no Klasse 3, so the plain-name
    # path could never reach CHE2's Kl.3 cells (its content failed coverage at ingest).
    assert resolve_grade("Chemie", 3, today=IN_WINDOW).competences == []


def test_che2_is_a_distinct_targetable_coverage_subject():
    """coverage_map / campaign_gaps must see CHE2 as its own subject (6 cells:
    Kl 3+4 × W/E/S) distinct from CHE — else a campaign can never fill it. Independent
    of block-store state: the cells come from the catalog, not from approved blocks."""
    cov = coverage_map()
    che_us = {s["code"] for s in cov["subjects"] if s["stufe"] == "Unterstufe"} & {"CHE", "CHE2"}
    assert che_us == {"CHE", "CHE2"}
    che2 = next(s for s in cov["subjects"]
                if s["code"] == "CHE2" and s["stufe"] == "Unterstufe")
    assert che2["cells_total"] == 6
    assert che2["name"] == store._DISPLAY_NAME_OVERRIDES[("Unterstufe", "CHE2")]
