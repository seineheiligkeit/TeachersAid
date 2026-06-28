"""The prose-provenance gate (History/GPB asset class) — the prose analogue of the
(c)-label figure gate. Advisory warnings: a history fact block must record its facts-source
(the mandatory-internal trust rule), and an embedded source's obligation must be coherent."""

from __future__ import annotations

from teachersaid.pipeline.prose_lint import lint_content
from teachersaid.schema import (
    Baustein,
    BlockProvenance,
    InfoBlock,
    ProvenanceSource,
    SubjectCompetenceModel,
    TaskBlock,
    WorksheetContent,
    WorksheetMeta,
)
from teachersaid.schema.competence import CompetenceDimension

FASSUNG = {
    "kurztitel": "AHS-Lehrplan (konsolidiert)", "bgbl": "BGBl. II Nr. 204/2024",
    "doknr": "NOR40264237", "valid_from": "2024-09-01", "valid_to": "2026-08-31",
}

GPB_MODEL = SubjectCompetenceModel(
    subject="Geschichte und politische Bildung",
    stufe="Unterstufe",
    dimensions=[CompetenceDimension(id="M", label="Methodenkompetenz"),
                CompetenceDimension(id="O", label="Orientierungskompetenz")],
)


def _wikipedia(role="facts", **kw):
    return ProvenanceSource(
        title="Wiener Kongress", url="https://de.wikipedia.org/wiki/Wiener_Kongress",
        publisher="Wikipedia (de)", licence="CC-BY-SA-4.0", retrieved="2026-06-28",
        role=role, **kw)


def _content(*intro_blocks, subject="Geschichte und politische Bildung", gpb_task=True):
    """A worksheet whose GPB-ness comes from a served GPB competence id (the robust signal)."""
    blocks = []
    if gpb_task:
        blocks.append(TaskBlock(
            id="t1", kind="open_response", prompt="Ordne die Ereignisse.",
            response={"mode": "lines", "n": 3}, cognitive_level="analyze",
            serves=[{"competence_id": "GPB.US.2.ALL.01", "relation": "exercises"}],
            est_minutes=6))
    meta = WorksheetMeta(title="Der Wiener Kongress", subject=subject,
                         stufe="Unterstufe", klasse=3, fassung=FASSUNG,
                         lehrplan_label=f"{subject}, 3. Klasse")
    return WorksheetContent(
        meta=meta, subject_model=GPB_MODEL, intro=list(intro_blocks),
        sections=[Baustein(id="s", title="Kern", blocks=blocks)])


def _info(id="i1", kind="prose", provenance=None, flags=None):
    return InfoBlock(id=id, kind=kind, content="Der Wiener Kongress ordnete 1814/15 Europa neu.",
                     provenance=provenance, flags=flags)


# --- (B) the facts-source-required rule (scoped to GPB ∪ historical_fact) -----
def test_gpb_fact_block_without_provenance_warns():
    _, warnings = lint_content(_content(_info()))
    assert any("ohne Provenienz" in w and "i1" in w for w in warnings)


def test_gpb_original_block_without_facts_source_warns():
    # has provenance, but original + no role="facts" → the mandatory-internal record is missing
    prov = BlockProvenance(expression_origin="original", sources=[_wikipedia(role="expression")])
    _, warnings = lint_content(_content(_info(provenance=prov)))
    assert any("role='facts'" in w for w in warnings)


def test_gpb_original_with_facts_source_is_clean():
    prov = BlockProvenance(expression_origin="original", sources=[_wikipedia()])
    _, warnings = lint_content(_content(_info(provenance=prov)))
    assert warnings == []


def test_callout_is_exempt_from_facts_rule():
    # a note/tip callout is scaffolding, not a factual assertion → no facts-source nag
    _, warnings = lint_content(_content(_info(kind="callout")))
    assert warnings == []


def test_non_gpb_prose_is_not_in_scope():
    # a Physik worksheet (no GPB serves, no historical_fact flag) → the gate stays quiet
    c = _content(_info(), subject="Physik", gpb_task=False)
    assert lint_content(c)[1] == []


def test_historical_fact_flag_pulls_non_gpb_block_into_scope():
    c = _content(_info(flags={"historical_fact": True}), subject="Geographie", gpb_task=False)
    _, warnings = lint_content(c)
    assert any("ohne Provenienz" in w for w in warnings)


# --- (A) consistency of an embedded source's obligation -----------------------
def test_adapted_cc_by_sa_trips_sharealike_and_redistributable():
    prov = BlockProvenance(expression_origin="adapted",
                           sources=[_wikipedia(role="expression")])  # redistributable defaults False
    _, warnings = lint_content(_content(_info(provenance=prov)))
    assert any("ShareAlike" in w for w in warnings)
    assert any("redistributable" in w for w in warnings)


def test_adapted_without_expression_source_warns():
    prov = BlockProvenance(expression_origin="adapted", sources=[_wikipedia(role="facts")])
    _, warnings = lint_content(_content(_info(provenance=prov)))
    assert any("keine role='expression'" in w for w in warnings)


def test_short_quote_is_fine_long_quote_warns():
    short = BlockProvenance(expression_origin="quoted", sources=[ProvenanceSource(
        title="Q", licence="public-domain", role="expression",
        author_death_year=1859, quote_span="… ein kurzes wörtliches Zitat …")])
    _, w_short = lint_content(_content(_info(provenance=short)))
    assert w_short == []  # PD short quote under Zitatrecht → clean

    long = BlockProvenance(expression_origin="quoted", sources=[ProvenanceSource(
        title="Q", licence="public-domain", role="expression",
        author_death_year=1859, quote_span="x" * 400)])
    _, w_long = lint_content(_content(_info(provenance=long)))
    assert any("langes wörtliches Zitat" in w for w in w_long)


def test_consistency_runs_regardless_of_subject():
    # (A) applies wherever provenance is present — even outside the history asset class
    prov = BlockProvenance(expression_origin="adapted", sources=[_wikipedia(role="expression")])
    c = _content(_info(provenance=prov), subject="Physik", gpb_task=False)
    assert any("ShareAlike" in w for w in lint_content(c)[1])
