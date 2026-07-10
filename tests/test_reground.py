"""Re-grounding the (c)-label-flagged GWB figures (c0081 / c0096 / c0097).

Two locks, both fully offline:
* the deterministic fetch-tool *parsers* (NOAA CO₂ · UNDP HDI · UN WPP continents ·
  World-Bank series/compare), fed small fixtures that mirror the real payloads — the
  `parse_lehrplan` / `fetch_matura` precedent (a tool parses, the model never invents);
* the committed re-grounded content items verify with **no (c)-label warning**, each
  data figure carrying a `data_source` citation or an honest `illustrative` flag — the
  deliverable, locked against catalog drift.
"""

from __future__ import annotations

import json

import teachersaid.config as config
from teachersaid.grounding import data_store as ds
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.verify import verify
from teachersaid.store.models import ReviewItem
from tools import fetch_noaa_co2, fetch_undp_hdi, fetch_un_wpp, fetch_worldbank

CLABEL = "ohne Quellenangabe"                       # figure_lint's (c)-label warning fragment
_UNRESOLVED = ("nicht im grounding/data-Katalog", "keine Serie", "liefert keine Werte")
ITEMS = ("c0081", "c0096", "c0097")
NEW_DATASETS = {
    "noaa_co2_mauna_loa": "verlauf", "undp_hdi": "vergleich",
    "un_wpp_kontinente_2024": "kontinente", "worldbank_fertilitaet": "vergleich",
}


# --- fetch-tool parsers (offline fixtures) -----------------------------------
def test_noaa_parse_annmean_and_grid():
    txt = ("# comment\n# year   mean   unc\n"
           "1959   315.98   0.12\n1960   316.91   0.12\n1970   325.68   0.11\n"
           "2020   414.21   0.10\n2024   424.61   0.10\n")
    annual = fetch_noaa_co2.parse_annmean(txt)
    assert annual[1960] == 316.91 and annual[2024] == 424.61
    cats, vals = fetch_noaa_co2.series_for_years(annual, [1960, 2024, 1990])   # 1990 absent → dropped
    assert cats == ["1960", "2024"] and vals == [316.9, 424.6]                 # rounded to 1 dp, in order


def test_undp_parse_hdi_uses_value_column_not_rank():
    csv_text = ("iso3,country,hdi_1990,hdi_2022,hdi_2023,hdi_rank_2023\n"
                "NER,Niger,0.216,0.411,0.419,188\n"
                "AUT,Austria,0.799,0.925,0.93,22\n"
                "XXX,Nowhere,..,..,..,..\n")
    cats, vals, year = fetch_undp_hdi.parse_hdi(
        csv_text, [("NER", "Niger"), ("AUT", "Österreich"), ("XXX", "Nirgendwo")])
    assert year == "2023"                          # latest hdi_<year> VALUE column, not hdi_rank_2023
    assert cats == ["Niger", "Österreich"] and vals == [0.419, 0.93]   # missing ".." row dropped


def test_wpp_parse_continents_filters_variant_and_locid():
    csv_text = (
        "SortOrder,LocID,Notes,ISO3_code,ISO2_code,SDMX_code,LocTypeID,LocTypeName,"
        "ParentID,Location,VarID,Variant,Time,MidPeriod,PopMale,PopFemale,PopTotal,PopDensity\n"
        "1,903,,,,903,,Region,900,Africa,2,Medium,2024,2024.5,,,1515140.849,\n"
        "2,903,,,,903,,Region,900,Africa,3,High,2024,2024.5,,,1516543.047,\n"     # wrong variant → skip
        "3,935,,,,935,,Region,900,Asia,2,Medium,2024,2024.5,,,4806898.007,\n"
        "4,40,,AUT,AT,40,4,Country,908,Austria,2,Medium,2024,2024.5,,,9159000,\n"   # country → skip
        "5,935,,,,935,,Region,900,Asia,2,Medium,2023,2023.5,,,4790000,\n")          # wrong year → skip
    cats, vals = fetch_un_wpp.parse_wpp(csv_text, [(903, "Afrika"), (935, "Asien")])
    assert cats == ["Afrika", "Asien"]
    assert vals == [1.52, 4.81]                    # PopTotal(thousands)/1e6 → billions, 2 dp; Medium/2024 only


def test_worldbank_series_at_years_projects_grid():
    payload = [{"page": 1}, [
        {"country": {"id": "WLD", "value": "World"}, "date": "2023", "value": 57.32},
        {"country": {"id": "WLD", "value": "World"}, "date": "2020", "value": 56.40},
        {"country": {"id": "WLD", "value": "World"}, "date": "1960", "value": 34.23},
        {"country": {"id": "WLD", "value": "World"}, "date": "1975", "value": None},   # null → skip
    ]]
    cats, vals = fetch_worldbank.series_at_years(payload, ["1960", "2020", "2023", "1990"], 1)
    assert cats == ["1960", "2020", "2023"] and vals == [34.2, 56.4, 57.3]             # 1990 absent → dropped


def test_worldbank_compare_latest_picks_newest_and_translates():
    payload = [{"page": 1}, [
        {"country": {"id": "NE", "value": "Niger"}, "date": "2023", "value": 6.10},
        {"country": {"id": "NE", "value": "Niger"}, "date": "2024", "value": 5.93},
        {"country": {"id": "AT", "value": "Austria"}, "date": "2024", "value": 1.31},
    ]]
    cats, vals, stand = fetch_worldbank.compare_latest(
        payload, ["NE", "AT"], {"NE": "Niger", "AT": "Österreich"}, 2)
    assert cats == ["Niger", "Österreich"] and vals == [5.93, 1.31] and stand == "2024"


# --- the curated new datasets (committed deliverables; lock against drift) -----
def test_new_datasets_present_clean_and_map():
    for did, series in NEW_DATASETS.items():
        d = ds.get_dataset(did)
        assert d is not None, f"{did} missing from catalog"
        assert d.source.redistributable and d.source.attribution      # ingest-gate clean
        assert d.source.licence and d.series                          # licence recorded + has data
        gen = "matplotlib:line" if series in ("verlauf", "welt_verlauf") else "matplotlib:bar_chart"
        spec, notes = ds.series_to_spec(ds_dataref(did, series), gen)
        assert not notes and spec.get("categories") and spec.get("values")

    # the World urbanisation TREND was added to the EXISTING dataset (minimal extension)
    urb = ds.get_dataset("worldbank_urbanisierung")
    assert "welt_verlauf" in urb.series and "vergleich" in urb.series   # both series present

    # loose sanity bounds (catch gross corruption without breaking on a legit re-fetch)
    asia = dict(zip(*_cats_vals("un_wpp_kontinente_2024", "kontinente")))["Asien"]
    assert 4.0 < asia < 5.5                                            # ~4.8 Mrd
    at_hdi = dict(zip(*_cats_vals("undp_hdi", "vergleich")))["Österreich"]
    assert 0.90 < at_hdi < 0.96                                        # ~0.93


def ds_dataref(dataset_id, series):
    from teachersaid.schema.datasets import DataRef
    return DataRef(dataset_id=dataset_id, series=series)


def _cats_vals(dataset_id, series):
    s = ds.get_dataset(dataset_id).series[series]
    return s["categories"], s["values"]


# --- the deliverable: the three items verify with NO (c)-label warning --------
def _load_item(cid) -> ReviewItem:
    p = config.REPO_ROOT / "runs" / "store" / f"{cid}.json"
    return ReviewItem.model_validate_json(p.read_text(encoding="utf-8"))


def test_flagged_items_verify_without_clabel_warning():
    for cid in ITEMS:
        item = _load_item(cid)
        assemble(item.content, item.resolution)          # re-grounds figures + stamps citations
        report = verify(item.content, item.resolution)
        assert not report.problems, f"{cid}: {report.problems}"
        clabel = [w for w in report.warnings if CLABEL in w]
        assert not clabel, f"{cid}: (c)-label warning still present: {clabel}"
        unresolved = [w for w in report.warnings if any(k in w for k in _UNRESOLVED)]
        assert not unresolved, f"{cid}: unresolved data_source: {unresolved}"


def test_every_data_figure_is_labelled_and_sourced_figures_cite():
    data_gens = {"matplotlib:bar_chart", "matplotlib:line", "matplotlib:scatter"}
    for cid in ITEMS:
        item = _load_item(cid)
        assemble(item.content, item.resolution)
        for a in item.content.assets:
            if (a.generator or "") not in data_gens:
                continue
            assert a.illustrative or a.data_source is not None, f"{cid}/{a.id} unlabelled"
            if a.data_source is not None:                # sourced → real citation resolved onto it
                assert a.data_source.attribution and "Datenquelle" in a.data_source.citation()
                assert not a.illustrative
