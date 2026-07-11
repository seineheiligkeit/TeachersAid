"""Wave C2 — the entity registry, the additive links, the corpus-global lint, and the
verwandte_module joy. Facts (names/dates) are select-never-author (cited rows); the lint is the
machine check that keeps them consistent across the whole corpus."""

from __future__ import annotations

import json

import pytest

from teachersaid.grounding import entities as ent
from teachersaid.library.sachverhalt_wiener_kongress import build_sachverhalt as build_wk
from teachersaid.pipeline import entity_lint as el
from teachersaid.schema.provenance import ProvenanceSource
from teachersaid.schema.sachverhalt import Actor, HistEvent, Sachverhalt

FACTS = ProvenanceSource(title="Quelle", role="facts")


def _mini(sid, *, timeline=(), actors=()) -> Sachverhalt:
    return Sachverhalt(id=sid, subject="Geschichte und politische Bildung", klasse_range=(3, 3),
                       topic="Testthema", sources=[FACTS],
                       timeline=list(timeline), actors=list(actors))


# --- the registry ------------------------------------------------------------
def test_registry_loads_and_every_entity_is_cited():
    reg = ent.load_registry()
    assert len(reg) >= 20                                  # the seeded corpus (~34)
    for e in reg.values():
        assert e.source and e.source.url and e.source.role == "facts", e.entity_id
        assert e.role and e.name                          # a one-line role + canonical name
    kinds = {e.kind for e in reg.values()}
    assert {"person", "event"} <= kinds                   # the corpus's two main kinds


def test_registry_integrity_rejects_duplicate_id(tmp_path, monkeypatch):
    dup = {"entities": [
        {"entity_id": "x", "kind": "person", "name": "A", "role": "r",
         "source": {"title": "t", "url": "u", "role": "facts"}},
        {"entity_id": "x", "kind": "person", "name": "B", "role": "r",
         "source": {"title": "t", "url": "u", "role": "facts"}},
    ]}
    (tmp_path / "d.json").write_text(json.dumps(dup), encoding="utf-8")
    monkeypatch.setattr(ent, "GROUNDING_ENTITIES", tmp_path)
    for fn in (ent.load_registry, ent._alias_index, ent._boundary_res):
        fn.cache_clear()
    try:
        with pytest.raises(ent.EntityError, match="doppelte entity_id"):
            ent.load_registry()
    finally:
        for fn in (ent.load_registry, ent._alias_index, ent._boundary_res):
            fn.cache_clear()


def test_year_range_semantics():
    assert ent.get_entity("napoleon-bonaparte").year_range() == (1769, 1821)   # person
    assert ent.get_entity("wiener-kongress").year_range() == (1814, 1815)      # event span
    assert ent.get_entity("voelkerschlacht-leipzig").year_range() == (1813, 1813)  # point
    assert ent.get_entity("wien").year_range() is None                         # place, no dates
    assert ent.get_entity("spinning-jenny").year_range() == (1764, 1764)       # work


def test_find_by_name_and_aliases():
    assert ent.find_by_name("Metternich").entity_id == "metternich"
    assert ent.find_by_name("napoleon").entity_id == "napoleon-bonaparte"      # alias, case-insensitive
    assert ent.find_by_name("nobody at all") is None


# --- additive linking: backward compatible ----------------------------------
def test_entity_id_is_additive_and_optional():
    # existing JSON (no entity_id) still validates — the field defaults to None
    assert HistEvent.model_validate({"at": 1789, "label": "x"}).entity_id is None
    assert Actor.model_validate({"name": "x", "role": "y"}).entity_id is None


def test_linked_flagship_roundtrips_and_resolves():
    sv = build_wk()
    assert Sachverhalt.model_validate(sv.model_dump()) == sv                   # round-trip
    linked = [a.entity_id for a in sv.actors] + [e.entity_id for e in sv.timeline]
    assert linked.count(None) == 0                                            # all WK actors/events linked
    for eid in linked:
        assert ent.get_entity(eid) is not None, eid                          # every link resolves


# --- per-module checks (drive the ingest gate) ------------------------------
def test_flagship_check_module_is_clean():
    problems, warnings = el.check_module(build_wk())
    assert problems == [] and warnings == []


def test_check_module_catches_unknown_link():
    sv = _mini("sv-bad-link", actors=[Actor(name="Wer", role="r", entity_id="does-not-exist")])
    problems, _ = el.check_module(sv)
    assert any("nicht gibt" in p for p in problems)


def test_check_module_catches_date_contradiction():
    # link a 1850 event to Napoleon (d. 1821) — a linked year the registry contradicts
    sv = _mini("sv-bad-date",
               timeline=[HistEvent(at=1850, label="Unfug", entity_id="napoleon-bonaparte")])
    problems, _ = el.check_module(sv)
    assert any("1850" in p and "widerspricht" in p for p in problems)


def test_check_module_advises_unlinked_alias():
    sv = _mini("sv-unlinked", actors=[Actor(name="Klemens von Metternich", role="r")])
    _p, warnings = el.check_module(sv)
    assert any("metternich" in w for w in warnings)                           # (b) advisory, not a problem


# --- corpus-global scan ------------------------------------------------------
def test_scan_corpus_clean_on_real_corpus():
    """The committed, linked corpus is consistent with the registry — a regression guard."""
    assert el.problems(el.scan_corpus()) == []


def test_scan_corpus_catches_planted_cross_module_conflict():
    # two modules link the SAME point-in-time event to DIFFERENT years → a real conflict
    a = _mini("sv-a", timeline=[HistEvent(at=1813, label="Leipzig", entity_id="voelkerschlacht-leipzig")])
    b = _mini("sv-b", timeline=[HistEvent(at=1913, label="Leipzig?!", entity_id="voelkerschlacht-leipzig")])
    findings = el.scan_corpus(sachverhalte=[a, b], texts=[])
    codes = {f.code for f in el.problems(findings)}
    assert "cross_module_conflict" in codes
    assert any(f.entity_id == "voelkerschlacht-leipzig" for f in findings)


def test_scan_corpus_author_date_cross_check():
    from teachersaid.library.texts import LORELEY                             # Heine, d. 1856 (matches)
    clean = el.scan_corpus(sachverhalte=[], texts=[LORELEY])
    assert not any(f.code == "author_date_mismatch" for f in clean)
    wrong = LORELEY.model_copy(deep=True)
    wrong.source.author_death_year = 1900                                     # planted disagreement
    findings = el.scan_corpus(sachverhalte=[], texts=[wrong])
    assert any(f.code == "author_date_mismatch" and f.entity_id == "heinrich-heine"
               for f in findings)


# --- the ingest gate ---------------------------------------------------------
def test_ingest_gate_blocks_registry_contradiction(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.sachverhaltstore import SachverhaltStore
    store = SachverhaltStore(tmp_path)
    # a 1700 event linked to Napoleon (b. 1769) — a year the registry contradicts
    bad = _mini("sv-bad-gate",
                timeline=[HistEvent(at=1700, label="Unfug", entity_id="napoleon-bonaparte")])
    with pytest.raises(ValueError, match="Entitäts-Register"):
        orch.ingest_sachverhalt(store, bad)
    # a clean module still stages, and the linked flagship stages too
    assert orch.ingest_sachverhalt(store, _mini("sv-ok")).status == "in_review"
    assert orch.ingest_sachverhalt(store, build_wk()).status == "in_review"


# --- the derived joy ---------------------------------------------------------
def test_verwandte_module_finds_shared_entity():
    a = _mini("sv-fr", actors=[Actor(name="Napoleon Bonaparte", role="r",
                                     entity_id="napoleon-bonaparte")])
    b = _mini("sv-wk")
    b.keywords = ["Napoleon", "Wien"]                                        # references, no explicit link
    rel = el.verwandte_module("napoleon-bonaparte", sachverhalte=[a, b], texts=[])
    ids = {r["module_id"]: r["via"] for r in rel}
    assert ids == {"sv-fr": "link", "sv-wk": "reference"}
    assert rel[0]["module_id"] == "sv-fr"                                     # links sort first


def test_verwandte_module_matches_text_author():
    from teachersaid.library.texts import LORELEY
    rel = el.verwandte_module("heinrich-heine", sachverhalte=[], texts=[LORELEY])
    assert rel and rel[0]["module_id"] == "deu-loreley" and rel[0]["via"] == "author"


def test_verwandte_module_unknown_entity_is_empty():
    assert el.verwandte_module("no-such-entity", sachverhalte=[], texts=[]) == []


def test_real_corpus_napoleon_relates_two_history_modules():
    rel = el.verwandte_module("napoleon-bonaparte")                          # live corpus
    ids = {r["module_id"] for r in rel}
    assert {"sv-franzoesische-revolution", "sv-wiener-kongress"} <= ids


# --- the API surface ---------------------------------------------------------
def test_api_entities():
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    client = TestClient(appmod.app)

    lst = client.get("/api/entities").json()
    assert len(lst) >= 20 and any(e["entity_id"] == "napoleon-bonaparte" for e in lst)
    persons = client.get("/api/entities", params={"kind": "person"}).json()
    assert persons and all(e["kind"] == "person" for e in persons)

    d = client.get("/api/entities/napoleon-bonaparte").json()
    assert d["dates"] == "1769–1821" and d["source"]["url"]
    assert {r["module_id"] for r in d["verwandte_module"]} >= {"sv-franzoesische-revolution"}
    assert client.get("/api/entities/nope").status_code == 404
