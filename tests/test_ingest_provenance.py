"""Phase 4 — ingest/HITL for expression provenance (History/GPB).

The rights gate at ingest (the `ingest_text` analogue), proven on the GPB path: an `original`
block from a Wikipedia facts-source stages clean (and the facts record survives the harvest);
a CC-BY-SA `adapted` block is permitted but ShareAlike-warned; a copyrighted `adapted` block
is rejected. Plus the rights methods and the deterministic Wikipedia source-record helper
(mocked — no network in tests)."""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import pytest

from teachersaid.schema.provenance import (
    SHORT_QUOTE_MAX_CHARS,
    BlockProvenance,
    ProvenanceSource,
)

TODAY = date(2026, 6, 28)
WP_FACTS = {
    "title": "Wiener Kongress",
    "url": "https://de.wikipedia.org/w/index.php?title=Wiener_Kongress&oldid=267935028",
    "publisher": "Wikipedia (de)", "licence": "CC-BY-SA-4.0",
    "licence_url": "https://creativecommons.org/licenses/by-sa/4.0/",
    "retrieved": "2026-06-28", "role": "facts",
}


def _body(provenance: dict):
    return {
        "intro": [],
        "sections": [{
            "id": "wk.s", "title": "Wiener Kongress", "throughline": "Gleichgewicht.",
            "talking_points": ["?"], "extensions": [],
            "blocks": [
                {"role": "info", "id": "wk.lern", "kind": "prose",
                 "content": "Nach Napoleons Niederlage ordnete der Kongress 1814/15 Europa neu.",
                 "provenance": provenance},
                {"role": "task", "id": "wk.t1", "kind": "source_analysis",
                 "prompt": "Untersuche die verlinkte Darstellung: Leitprinzip?",
                 "response": {"mode": "lines", "n": 5}, "cognitive_level": "analyze",
                 "dimensions": ["HME"],
                 "serves": [{"competence_id": "GPB.US.3.ALL.01", "relation": "exercises"}],
                 "est_minutes": 10, "answer_key": "Gleichgewicht der Mächte."},
            ],
        }],
    }


@pytest.fixture
def stores(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.store.blockstore import BlockStore
    from teachersaid.store.repository import ReviewStore
    return ReviewStore(tmp_path / "store"), BlockStore(tmp_path / "blocks")


def _ingest(stores, body, title="Der Wiener Kongress"):
    from teachersaid.pipeline import orchestrator as orch
    store, blocks = stores
    return orch.ingest_generated(
        store, blocks, "Geschichte und politische Bildung", 3,
        scope_label="Der Wiener Kongress", title=title,
        kernfrage="Wie ordnet der Kongress Europa neu?", body=body,
        render=False, today=TODAY)


# --- the ingest rights gate, on the GPB path ---------------------------------
def test_original_from_facts_stages_clean_and_preserves_facts_record(stores):
    item, n = _ingest(stores, _body({"expression_origin": "original", "sources": [WP_FACTS]}))
    assert item.error is None and item.verify_problems == []
    assert n == 2  # both blocks harvested
    lern = next(b for b in item.content.iter_blocks() if b.id == "wk.lern")
    assert lern.provenance.expression_origin == "original"
    assert lern.provenance.facts_sources()[0].url.endswith("oldid=267935028")
    assert lern.provenance.attribution_required is False  # clean for students
    # the harvested library block keeps its provenance too
    _, block_store = stores
    hb = next(b for b in block_store.list() if b.id.endswith("wk.lern"))
    assert hb.block.provenance.facts_sources()  # survived the harvest round-trip


def test_cc_by_sa_adapted_is_permitted_but_sharealike_warned(stores):
    prov = {"expression_origin": "adapted",
            "sources": [{**WP_FACTS, "role": "expression", "redistributable": True}]}
    item, n = _ingest(stores, _body(prov))
    assert item.error is None and n == 2             # permitted (CC-BY-SA is redistributable)
    assert any("ShareAlike" in w for w in item.verify_warnings)


def test_copyrighted_adapted_is_rejected_by_rights_gate(stores):
    prov = {"expression_origin": "adapted", "sources": [{
        "title": "Schulbuch 3 (Verlag XY)", "licence": "© alle Rechte vorbehalten",
        "role": "expression", "redistributable": False}]}
    item, n = _ingest(stores, _body(prov))
    assert item.error is not None and "rights" in item.error
    assert n == 0  # nothing harvested from a rights-failing worksheet


# --- rights methods (unit) ---------------------------------------------------
def test_rights_clear_pd_pma_and_cc_and_copyright():
    pd_old = ProvenanceSource(title="Q", licence="public-domain", role="expression",
                              author_death_year=1859)
    assert pd_old.rights_clear(2026)[0] is True                 # 167y p.m.a. → clear
    pd_recent = ProvenanceSource(title="Q", licence="public-domain", role="expression",
                                 author_death_year=1990)
    assert pd_recent.rights_clear(2026)[0] is False             # <70y → still protected (AT)
    pd_noyear = ProvenanceSource(title="Q", licence="public-domain", role="expression")
    assert pd_noyear.rights_clear(2026)[0] is False             # PD but no death year
    assert ProvenanceSource(title="Q", licence="CC-BY-SA-4.0",
                            role="expression").rights_clear(2026)[0] is True
    assert ProvenanceSource(title="Q", licence="© reserved",
                            role="expression").rights_clear(2026)[0] is False
    assert ProvenanceSource(title="Q", role="expression",
                            redistributable=True).rights_clear(2026)[0] is True


def test_rights_gate_short_quote_rides_zitatrecht():
    short = BlockProvenance(expression_origin="quoted", sources=[ProvenanceSource(
        title="© Moderner Text", role="expression", redistributable=False,
        quote_span="x" * (SHORT_QUOTE_MAX_CHARS - 1))])
    assert short.rights_gate(2026)[0] is True                   # short citation → permitted
    long = BlockProvenance(expression_origin="quoted", sources=[ProvenanceSource(
        title="© Moderner Text", role="expression", redistributable=False,
        quote_span="x" * (SHORT_QUOTE_MAX_CHARS + 50))])
    assert long.rights_gate(2026)[0] is False                   # long verbatim → needs a basis
    assert BlockProvenance(expression_origin="original").rights_gate(2026)[0] is True


# --- the Wikipedia source-record helper (mocked — no network) ----------------
def _load_fetch():
    spec = importlib.util.spec_from_file_location(
        "fetch_wikipedia", str(Path(__file__).resolve().parent.parent / "tools" / "fetch_wikipedia.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_fetch_wikipedia_builds_permalink_facts_record(monkeypatch):
    m = _load_fetch()
    monkeypatch.setattr(m, "_get_json", lambda url: {
        "titles": {"canonical": "Wiener_Kongress"},
        "content_urls": {"desktop": {"page": "https://de.wikipedia.org/wiki/Wiener_Kongress"}},
        "revision": "267935028", "timestamp": "2026-06-14T14:24:16Z"})
    src = m.fetch_source("Wiener Kongress", lang="de", retrieved="2026-06-28")
    assert src.role == "facts"                                  # consult-only by default
    assert src.licence == "CC-BY-SA-4.0" and src.publisher == "Wikipedia (de)"
    assert src.url == ("https://de.wikipedia.org/w/index.php?"
                       "title=Wiener_Kongress&oldid=267935028")  # permalink to the exact revision
    assert src.title == "Wiener Kongress"
