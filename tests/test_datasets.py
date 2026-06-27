"""Grounded-facts data layer + the population-pyramid recipe (the convergent spike).

Covers: the curated Statistik-Austria dataset (locked like the master library), the
data_store resolver (select-never-author citation), the (c)-label verify gate, the
pyramid recipe, the DatasetStore + ingest gate, citation rendering, and the API tab.
"""

from __future__ import annotations

import json

import pytest

from teachersaid.grounding import data_store as ds
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.figure_lint import lint_content
from teachersaid.schema.assets import Asset
from teachersaid.schema.datasets import DataRef, Dataset, SourceRef

PNG = b"\x89PNG\r\n\x1a\n"
REAL_ID = "statistik_austria_bevstand_2024"


# --- the curated dataset (a committed deliverable; lock it against drift) ------
def test_real_dataset_present_and_correct():
    d = ds.get_dataset(REAL_ID)
    assert d is not None
    assert d.totals["gesamt"] == 9158750            # Statistik Austria, 1.1.2024
    assert d.totals["männlich"] + d.totals["weiblich"] == d.totals["gesamt"]
    assert d.source.licence == "CC BY 4.0" and d.source.redistributable
    pyr = d.series["pyramide_5j"]
    assert pyr["kind"] == "population_pyramid"
    assert len(pyr["age_groups"]) == len(pyr["male"]) == len(pyr["female"]) == 18
    assert sum(pyr["male"]) + sum(pyr["female"]) == d.totals["gesamt"]


def test_resolve_dataref_fills_citation():
    ref, notes = ds.resolve_dataref(DataRef(dataset_id=REAL_ID, series="pyramide_5j"))
    assert not notes
    assert ref.attribution and "Statistik Austria" in ref.attribution
    assert ref.stand == "2024-01-01"
    assert "Statistik Austria" in ref.citation() and "Stand" in ref.citation()


def test_resolve_dataref_honest_gaps():
    _, notes = ds.resolve_dataref(DataRef(dataset_id="does_not_exist"))
    assert any("nicht im grounding/data-Katalog" in n for n in notes)
    _, notes2 = ds.resolve_dataref(DataRef(dataset_id=REAL_ID, series="nope"))
    assert any("keine Serie" in n for n in notes2)


def test_resolve_never_trusts_authored_citation():
    # a hand-written, wrong attribution must be OVERWRITTEN from the vetted dataset
    ref, _ = ds.resolve_dataref(DataRef(dataset_id=REAL_ID, series="pyramide_5j",
                                        attribution="Erfundene Quelle"))
    assert ref.attribution != "Erfundene Quelle"
    assert "Statistik Austria" in ref.attribution


# --- the population-pyramid recipe -------------------------------------------
def test_population_pyramid_renders(tmp_path):
    d = ds.get_dataset(REAL_ID)
    s = d.series["pyramide_5j"]
    a = Asset(id="pyr", role="figure", generator="matplotlib:population_pyramid",
              spec={"age_groups": s["age_groups"], "male": s["male"], "female": s["female"],
                    "title": d.title})
    p = build_asset(a, outdir=tmp_path)
    assert p.read_bytes()[:8] == PNG and p.stat().st_size > 2000


def test_demographic_intent_maps_to_pyramid():
    from teachersaid.schema.chart_choose import choose_representation
    gen, spec = choose_representation("demographic", {
        "age_groups": ["0–4", "5–9"], "male": [1, 2], "female": [3, 4]})
    assert gen == "matplotlib:population_pyramid"
    assert spec["male"] == [1, 2] and spec["female"] == [3, 4]


def test_gen_data_figure_demographic_roundtrip():
    from teachersaid.schema.generation_views import GenDataFigure, data_figure_to_asset
    a = data_figure_to_asset(GenDataFigure(
        id="f", intent="demographic", categories=["0–4", "5–9"], male=[1, 2], female=[3, 4],
        data_source=DataRef(dataset_id=REAL_ID, series="pyramide_5j")))
    assert a.generator == "matplotlib:population_pyramid"
    assert a.spec["age_groups"] == ["0–4", "5–9"]
    assert a.data_source and a.data_source.dataset_id == REAL_ID


# --- the (c)-label gate (figure_lint) ----------------------------------------
def _content(*assets):
    from types import SimpleNamespace
    return SimpleNamespace(assets=list(assets))


def _bar(aid, vals, **kw):
    return Asset(id=aid, role="figure", generator="matplotlib:bar_chart",
                 spec={"categories": [f"c{i}" for i in range(len(vals))], "values": vals}, **kw)


def test_lint_flags_unlabelled_real_numbers():
    _, w = lint_content(_content(_bar("u", [14.4, 16.8, 20.6, 21.2])))
    assert any("ohne Quellenangabe" in x for x in w)


def test_lint_clean_when_illustrative():
    _, w = lint_content(_content(_bar("i", [14.4, 16.8, 20.6], illustrative=True)))
    assert not w


def test_lint_clean_when_sourced():
    a = _bar("s", [14.4, 16.8, 20.6],
             data_source=DataRef(dataset_id=REAL_ID, series="altersgruppen_breit"))
    _, w = lint_content(_content(a))
    assert not w


def test_lint_warns_on_unresolvable_source():
    a = _bar("bad", [1.1, 2.2, 3.3], data_source=DataRef(dataset_id="ghost"))
    _, w = lint_content(_content(a))
    assert any("nicht im grounding/data-Katalog" in x for x in w)


def test_lint_exempts_pure_math_figures():
    fg = Asset(id="m", role="figure", generator="matplotlib:function_graph",
               spec={"m": 2, "b": 1})
    _, w = lint_content(_content(fg))
    assert not w


# --- citation grounding + rendering ------------------------------------------
def test_ground_data_stamps_citation_and_fills_real_values():
    from types import SimpleNamespace

    from teachersaid.pipeline.data_ground import ground_data
    # authored WRONG values + a data_source → grounding must overwrite with REAL data
    a = Asset(id="abb", role="figure", generator="matplotlib:population_pyramid",
              spec={"male": [1, 2, 3], "female": [4, 5, 6], "title": "keep me"},
              data_source=DataRef(dataset_id=REAL_ID, series="pyramide_5j"))
    notes = ground_data(SimpleNamespace(assets=[a]))
    assert not notes
    assert a.data_source.attribution and "Statistik Austria" in a.data_source.attribution
    d = ds.get_dataset(REAL_ID).series["pyramide_5j"]
    assert a.spec["male"] == d["male"] and a.spec["female"] == d["female"]   # real, not authored
    assert a.spec["age_groups"] == d["age_groups"]
    assert a.spec["title"] == "keep me"                                      # presentation kept


# --- discovery: data ⇄ ideas interplay ---------------------------------------
def test_relevant_datasets_by_subject_topic_competence():
    assert any(d.id == REAL_ID for d in ds.relevant_datasets(subject="GWB"))
    assert not ds.relevant_datasets(subject="PHY")                          # not tagged
    assert any(d.id == REAL_ID for d in ds.relevant_datasets(topic="Altersstruktur und Demografie"))
    assert any(d.id == REAL_ID for d in ds.relevant_datasets(competences=["GWB.US.3.OST.01"]))
    assert ds.relevant_datasets()                                           # no filter → all


def test_series_to_spec_maps_and_warns():
    spec, notes = ds.series_to_spec(DataRef(dataset_id=REAL_ID, series="pyramide_5j"),
                                    "matplotlib:population_pyramid")
    assert not notes and set(spec) == {"age_groups", "male", "female"}
    spec2, _ = ds.series_to_spec(DataRef(dataset_id=REAL_ID, series="altersgruppen_breit"),
                                 "matplotlib:bar_chart")
    assert "categories" in spec2 and "values" in spec2
    _, n1 = ds.series_to_spec(DataRef(dataset_id="ghost"), "matplotlib:bar_chart")
    assert any("Katalog" in x for x in n1)
    _, n2 = ds.series_to_spec(DataRef(dataset_id=REAL_ID, series="nope"), "matplotlib:bar_chart")
    assert any("Serie" in x for x in n2)


def test_format_available_datasets_brief():
    brief = ds.format_available_datasets(ds.relevant_datasets(subject="GWB"))
    assert REAL_ID in brief and "data_source" in brief and "pyramide_5j" in brief
    assert ds.format_available_datasets([]) == ""


def test_pdf_prints_quelle(tmp_path):
    import fitz

    from teachersaid.grounding import lehrplan_store as ls
    from teachersaid.rendering._document import build_pdf
    from teachersaid.schema.blocks import InfoBlock
    from teachersaid.schema.worksheet import WorksheetContent, WorksheetMeta

    d = ds.get_dataset(REAL_ID)
    s = d.series["pyramide_5j"]
    ref, _ = ds.resolve_dataref(DataRef(dataset_id=REAL_ID, series="pyramide_5j"))
    asset = Asset(id="abb", role="figure", generator="matplotlib:population_pyramid",
                  spec={"age_groups": s["age_groups"], "male": s["male"], "female": s["female"]},
                  data_source=ref)
    png = build_asset(asset, outdir=tmp_path)
    meta = WorksheetMeta(title="Demografie", subject="Geographie und wirtschaftliche Bildung",
                         stufe="Unterstufe", klasse=3, fassung=ls.get_fassung(), lehrplan_label="x")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model("GWB"),
        intro=[InfoBlock(id="f", kind="figure", content="Pyramide", asset_refs=["abb"])],
        sections=[], assets=[asset])
    out = build_pdf(content, "student", tmp_path / "s.pdf", assets={"abb": png})
    text = "".join(page.get_text() for page in fitz.open(out))
    assert "Quelle:" in text and "Statistik Austria" in text


# --- DatasetStore + ingest gate ----------------------------------------------
def _toy_dataset(redistributable=True, attribution="Quelle X"):
    return Dataset(id="toy", title="Toy", unit="x",
                   source=SourceRef(publisher="P", title="T", redistributable=redistributable,
                                    attribution=attribution, licence="CC BY 4.0"),
                   series={"a": {"label": "A", "groups": ["x"], "counts": [1]}})


def test_dataset_store_roundtrip_and_status_preserve(tmp_path):
    from teachersaid.store.datasetstore import DatasetRecord, DatasetStore
    store = DatasetStore(tmp_path)
    store.upsert(DatasetRecord(id="toy", dataset=_toy_dataset()))
    assert store.get("toy").status == "in_review"
    store.set_status("toy", "approved")
    store.upsert(DatasetRecord(id="toy", dataset=_toy_dataset()))   # re-seed
    assert store.get("toy").status == "approved"                    # not un-approved
    assert store.approved() and store.list(status="approved")


def test_ingest_dataset_gates_licence(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.datasetstore import DatasetStore
    store = DatasetStore(tmp_path)
    rec = orch.ingest_dataset(store, _toy_dataset())
    assert rec.status == "in_review"
    with pytest.raises(ValueError, match="redistributable"):
        orch.ingest_dataset(store, _toy_dataset(redistributable=False))
    with pytest.raises(ValueError, match="attribution"):
        orch.ingest_dataset(store, _toy_dataset(attribution=""))


def test_seed_datasets_stages_real(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.datasetstore import DatasetStore
    store = DatasetStore(tmp_path)
    seeded = orch.seed_datasets(store)
    assert any(r.id == REAL_ID for r in seeded)
    assert all(r.status == "in_review" for r in seeded)


def test_api_datasets(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.store.datasetstore import DatasetStore

    appmod.DATASETS = DatasetStore(tmp_path / "datasets")
    appmod.orch.seed_datasets(appmod.DATASETS)
    client = TestClient(appmod.app)

    lst = client.get("/api/datasets").json()
    assert lst and any(d["id"] == REAL_ID for d in lst)
    d = client.get(f"/api/datasets/{REAL_ID}").json()
    assert d["redistributable"] and "pyramide_5j" in d["series"]
    # the figure preview serves a PNG
    r = client.get(f"/api/datasets/{REAL_ID}/figure", params={"series": "pyramide_5j"})
    assert r.status_code == 200 and r.content[:8] == PNG
    # approve flips status
    assert client.post(f"/api/datasets/{REAL_ID}/approve").json()["status"] == "approved"
    assert all(x["id"] != REAL_ID for x in client.get("/api/datasets?status=in_review").json())


def test_feedback_accepts_dataset_kind():
    from teachersaid.store.feedbackstore import TARGET_KINDS
    assert "dataset" in TARGET_KINDS


# --- the curated GWB catalog (committed deliverables; lock against drift) ------
_CURATED = [
    "statistik_austria_bevstand_2024", "statistik_austria_bundeslaender_2024",
    "worldbank_at_bevoelkerung", "worldbank_at_alterung", "worldbank_urbanisierung",
    "worldbank_bip_pro_kopf", "worldbank_co2_pro_kopf", "geosphere_klima_normal_1991_2020",
]


def test_curated_catalog_present_and_clean():
    ids = {d.id for d in ds.list_datasets()}
    assert set(_CURATED) <= ids
    for cid in _CURATED:
        d = ds.get_dataset(cid)
        assert d.source.redistributable and d.source.attribution      # embeddable + cited
        assert "CC BY" in (d.source.licence or "")
        assert "GWB" in d.subjects and d.series                       # discoverable + has data


def test_bundeslaender_sums_to_national_total():
    bl = ds.get_dataset("statistik_austria_bundeslaender_2024").series["bevoelkerung"]
    assert len(bl["groups"]) == 9 and sum(bl["counts"]) == 9158750


def test_geosphere_normals_shape():
    wien = ds.get_dataset("geosphere_klima_normal_1991_2020").series["wien"]
    assert len(wien["temp"]) == 12 and len(wien["precip"]) == 12
    spec, notes = ds.series_to_spec(
        DataRef(dataset_id="geosphere_klima_normal_1991_2020", series="bregenz"),
        "matplotlib:climate_diagram")
    assert not notes and set(spec) == {"months", "temp", "precip"}
