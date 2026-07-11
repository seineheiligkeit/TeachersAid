"""Offline parser locks and curated-output checks for roadmap T4."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from teachersaid.grounding import data_store, geo_store
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.figure_lint import lint_content
from teachersaid.schema.assets import Asset
from teachersaid.schema.datasets import DataRef
from tools.fetch_geo_boundaries import simplify, validate
from tools.fetch_statistik_austria_health import parse_life_expectancy
from tools.fetch_statistik_austria_regional import district_names, parse_district_population

FIXTURES = Path(__file__).parent / "fixtures"


def test_health_parser_selects_austria_age_zero_and_preserves_decimal_values():
    dataset = parse_life_expectancy(
        (FIXTURES / "statistik_health.csv").read_text(encoding="utf-8"), "2026-07-11")
    male = dataset["series"]["lebenserwartung_maennlich"]
    female = dataset["series"]["lebenserwartung_weiblich"]
    assert male == {"label": "Lebenserwartung bei Geburt – männlich",
                    "years": [2023, 2024], "values": [79.4, 79.8]}
    assert female["values"] == [84.2, 84.3]
    assert dataset["series"]["vergleich_aktuell"]["values"] == [79.8, 84.3]
    assert dataset["source"]["licence"] == "CC BY 4.0"
    assert dataset["subjects"][0] == "BIO"
    assert dataset["competences"] == ["BIO.US.x.WIS.02", "BIO.US.x.ERK.04"]


def _district_fixture() -> tuple[str, str]:
    return ((FIXTURES / "statistik_bezirke.csv").read_text(encoding="utf-8"),
            (FIXTURES / "statistik_bezirke.geojson").read_text(encoding="utf-8"))


def test_district_parser_aggregates_municipalities_and_keeps_vienna_district():
    facts, boundaries = _district_fixture()
    names = district_names(boundaries)
    dataset = parse_district_population(facts, names, "2026-07-11")
    series = dataset["series"]["bevoelkerung"]
    assert series["region_codes"] == ["101", "103", "901"]
    assert series["groups"][-1] == "Wien 1.,Innere Stadt"
    assert series["counts"] == [220, 100, 500]
    assert dataset["totals"]["gesamt"] == 820
    assert series["geo_id"] == "at_bezirke_2025"


def test_district_parser_fails_when_population_and_boundary_codes_diverge():
    facts, boundaries = _district_fixture()
    with pytest.raises(ValueError, match="absent from WFS"):
        parse_district_population(facts.replace("GRGEMAKT-10101", "GRGEMAKT-99901", 1),
                                  district_names(boundaries), "2026-07-11")


def test_boundary_validation_and_simplification_are_offline_and_deterministic():
    _, boundaries = _district_fixture()
    cfg = {"name_field": "g_name", "expected_n": 3,
           "expected_names": ["Eisenstadt(Stadt)", "Wien 1.,Innere Stadt"]}
    raw = validate(boundaries.encode(), cfg)
    before = len(raw["features"][0]["geometry"]["coordinates"][0])
    reduced = simplify(raw, 0.01)
    ring = reduced["features"][0]["geometry"]["coordinates"][0]
    assert len(ring) < before and ring[0] == ring[-1] and len(ring) >= 4
    assert reduced["features"][0]["properties"]["g_id"] == "101"


def test_curated_t4_datasets_and_all_117_boundaries_are_joinable():
    health = data_store.get_dataset("statistik_austria_lebenserwartung_2002_2024")
    districts = data_store.get_dataset("statistik_austria_bezirke_2024")
    assert health is not None and "BIO" in health.subjects
    assert set(health.competences) == {"BIO.US.x.WIS.02", "BIO.US.x.ERK.04"}
    assert districts is not None and districts.totals["gesamt"] == 9158750
    series = districts.series["bevoelkerung"]
    boundaries = geo_store.load_boundaries("at_bezirke_2025")
    assert len(series["groups"]) == len(boundaries) == 116
    assert set(series["groups"]) == set(boundaries)
    assert sum(series["counts"]) == districts.totals["gesamt"]


def test_bio_line_and_district_map_are_sourced_lint_clean_and_render(tmp_path):
    health = data_store.get_dataset("statistik_austria_lebenserwartung_2002_2024")
    hseries = health.series["lebenserwartung_maennlich"]
    line = Asset(
        id="bio-life", role="figure", generator="matplotlib:line",
        spec={"categories": hseries["years"], "values": hseries["values"],
              "xlabel": "Jahr", "ylabel": "Jahre", "title": health.title},
        data_source=DataRef(dataset_id=health.id, series="lebenserwartung_maennlich"),
    )
    districts = data_store.get_dataset("statistik_austria_bezirke_2024")
    dseries = districts.series["bevoelkerung"]
    district_map = Asset(
        id="district-map", role="figure", generator="matplotlib:choropleth_map",
        spec={"geo_id": dseries["geo_id"],
              "values": dict(zip(dseries["groups"], dseries["counts"])),
              "value_label": "Personen", "show_labels": False,
              "title": districts.title},
        data_source=DataRef(dataset_id=districts.id, series="bevoelkerung"),
    )
    assert lint_content(SimpleNamespace(assets=[line, district_map])) == ([], [])
    assert build_asset(line, outdir=tmp_path).stat().st_size > 2000
    assert build_asset(district_map, outdir=tmp_path).stat().st_size > 2000


def test_dataset_dashboard_selects_choropleth_for_district_series():
    from teachersaid.api.app import _dataset_figure_asset
    from teachersaid.store.datasetstore import DatasetRecord

    dataset = data_store.get_dataset("statistik_austria_bezirke_2024")
    asset = _dataset_figure_asset(DatasetRecord(id=dataset.id, dataset=dataset), "bevoelkerung")
    assert asset.generator == "matplotlib:choropleth_map"
    assert asset.spec["geo_id"] == "at_bezirke_2025" and not asset.spec["show_labels"]
    assert asset.data_source.dataset_id == dataset.id
