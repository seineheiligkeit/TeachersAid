"""Deterministic fetch of World Bank Open Data indicators → grounding/data/.

World Bank Open Data is CC BY 4.0 (redistribution permitted with attribution) and its
API is plain JSON, so it's the cleanest global/cross-country source for GWB. No LLM in
the fact path — a configured indicator is fetched, parsed, and written with its citation.

Two dataset shapes:
* **time series** (one country, all years) — e.g. Austria's population / share 65+ → a trend;
* **comparison** (many countries, latest available year) — urbanisation / GDP p.c. / CO₂ p.c.

    python tools/fetch_worldbank.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "teachersaid" / "grounding" / "data"
API = "https://api.worldbank.org/v2"

# German display names for the countries we compare (fallback: the WB English name)
_DE = {
    "AT": "Österreich", "DE": "Deutschland", "CH": "Schweiz", "IT": "Italien",
    "US": "USA", "CN": "China", "IN": "Indien", "NG": "Nigeria", "BR": "Brasilien",
    # + the fertility-comparison countries (build_extension)
    "NE": "Niger", "ML": "Mali", "AO": "Angola", "CD": "DR Kongo", "SO": "Somalia",
    "JP": "Japan", "KR": "Südkorea",
}
COMPARE = ["AT", "DE", "CH", "IT", "US", "CN", "IN", "NG"]

# --- build_extension config (additive, does NOT re-fetch the six curated datasets) --------
# The World urbanisation TREND (1960→) added to the existing worldbank_urbanisierung dataset,
# projected onto the worksheet figure's decade grid; and a fertility-by-country dataset.
URB_YEARS = ["1960", "1970", "1980", "1990", "2000", "2010", "2020", "2023"]
FERT_ORDER = ["NE", "ML", "AO", "CD", "SO", "DE", "JP", "AT", "KR", "IT"]

# id, kind, indicator, title, unit, round, subjects, keywords, competences
DATASETS = [
    ("worldbank_at_bevoelkerung", "series", "AT", "SP.POP.TOTL",
     "Bevölkerung Österreichs im Zeitverlauf", "Personen", 0,
     ["GWB", "MAT"], ["Bevölkerung", "Bevölkerungsentwicklung", "Wachstum", "Demografie", "Zeitreihe", "Daten"],
     ["GWB.US.3.OST.01"]),
    ("worldbank_at_alterung", "series", "AT", "SP.POP.65UP.TO.ZS",
     "Anteil der über 65-Jährigen in Österreich", "%", 1,
     ["GWB", "MAT"], ["Alterung", "Überalterung", "Demografie", "Pensionen", "Altersstruktur", "65", "Daten"],
     ["GWB.US.3.OST.01"]),
    ("worldbank_urbanisierung", "compare", None, "SP.URB.TOTL.IN.ZS",
     "Verstädterung im Ländervergleich (Anteil Stadtbevölkerung)", "%", 1,
     ["GWB", "MAT"], ["Verstädterung", "Urbanisierung", "Stadt", "Land", "Disparitäten", "global", "Daten"],
     []),
    ("worldbank_bip_pro_kopf", "compare", None, "NY.GDP.PCAP.CD",
     "BIP pro Kopf im Ländervergleich", "US-Dollar", 0,
     ["GWB", "MAT"], ["BIP", "Wirtschaft", "Wohlstand", "Einkommen", "Disparitäten", "Ländervergleich", "global", "Daten"],
     []),
    ("worldbank_co2_pro_kopf", "compare", None, "EN.GHG.CO2.PC.CE.AR5",
     "CO₂-Ausstoß pro Kopf im Ländervergleich", "t CO₂/Kopf", 1,
     ["GWB", "MAT", "PHY"], ["CO2", "Klima", "Klimawandel", "Emissionen", "Umwelt", "Disparitäten", "global", "Daten"],
     []),
]


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-WB-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _round(v: float, nd: int):
    return int(round(v)) if nd == 0 else round(v, nd)


def _series(country: str, indicator: str, nd: int) -> tuple[list[str], list, str]:
    data = _get_json(f"{API}/country/{country}/indicator/{indicator}?format=json&per_page=20000")
    rows = [r for r in (data[1] or []) if r["value"] is not None]
    rows.sort(key=lambda r: r["date"])
    years = [r["date"] for r in rows]
    vals = [_round(r["value"], nd) for r in rows]
    stand = years[-1] if years else ""
    return years, vals, stand


def _compare(indicator: str, nd: int) -> tuple[list[str], list, str]:
    ids = ";".join(COMPARE)
    data = _get_json(f"{API}/country/{ids}/indicator/{indicator}?format=json&date=2015:2024&per_page=20000")
    latest: dict[str, dict] = {}
    for r in (data[1] or []):
        if r["value"] is None:
            continue
        c = r["country"]["id"]
        if c not in latest or r["date"] > latest[c]["date"]:
            latest[c] = r
    cats, vals, stand = [], [], ""
    for c in COMPARE:
        r = latest.get(c)
        if not r:
            continue
        cats.append(_DE.get(c, r["country"]["value"]))
        vals.append(_round(r["value"], nd))
        stand = max(stand, r["date"])
    return cats, vals, stand


# --- pure parse helpers (offline-testable: take an already-fetched WB payload) ----------
def parse_rows(payload) -> list[dict]:
    """A WB `[meta, rows]` payload → the value-bearing rows (skip nulls)."""
    return [r for r in (payload[1] or []) if r.get("value") is not None]


def series_at_years(payload, years: list[str], nd: int) -> tuple[list[str], list]:
    """Project a one-country time series onto a fixed set of years (the figure's grid)."""
    by_year = {r["date"]: r["value"] for r in parse_rows(payload)}
    cats = [y for y in years if y in by_year]
    vals = [_round(by_year[y], nd) for y in cats]
    return cats, vals


def compare_latest(payload, order: list[str], de_names: dict, nd: int) -> tuple[list[str], list, str]:
    """Latest available value per country, in the given order (the comparison-figure shape)."""
    latest: dict[str, dict] = {}
    for r in parse_rows(payload):
        c = r["country"]["id"]
        if c not in latest or r["date"] > latest[c]["date"]:
            latest[c] = r
    cats, vals, stand = [], [], ""
    for c in order:
        r = latest.get(c)
        if not r:
            continue
        cats.append(de_names.get(c, r["country"]["value"]))
        vals.append(_round(r["value"], nd))
        stand = max(stand, r["date"])
    return cats, vals, stand


def build_extension(retrieved: str) -> list[dict]:
    """Additive pull (task: re-ground the c0081 figures) — extend the EXISTING urbanisation
    dataset with a World trend series (its curated `vergleich` series is preserved from disk,
    NOT re-fetched), and add a fertility-by-country dataset. The other five World-Bank
    datasets are left untouched (no value drift on unrelated committed records)."""
    out = []
    # 1) worldbank_urbanisierung += welt_verlauf (World, SP.URB.TOTL.IN.ZS over time)
    urb_path = OUT_DIR / "worldbank_urbanisierung.json"
    urb = json.loads(urb_path.read_text(encoding="utf-8"))
    payload = _get_json(f"{API}/country/WLD/indicator/SP.URB.TOTL.IN.ZS?format=json&per_page=20000")
    cats, vals = series_at_years(payload, URB_YEARS, 1)
    urb["series"]["welt_verlauf"] = {
        "label": "Anteil Stadtbevölkerung weltweit (%)", "categories": cats, "values": vals}
    print(f"[fetch] worldbank_urbanisierung += welt_verlauf  {cats[0]}–{cats[-1]} ({len(cats)} pts)")
    out.append(urb)
    # 2) worldbank_fertilitaet (SP.DYN.TFRT.IN, the 10 countries of the c0081 fertility figure)
    ids = ";".join(FERT_ORDER)
    fp = _get_json(f"{API}/country/{ids}/indicator/SP.DYN.TFRT.IN?format=json&date=2015:2024&per_page=20000")
    fcats, fvals, fstand = compare_latest(fp, FERT_ORDER, _DE, 2)
    print(f"[fetch] worldbank_fertilitaet  {len(fcats)} countries, Stand {fstand}")
    out.append({
        "id": "worldbank_fertilitaet",
        "title": "Gesamtfertilitätsrate im Ländervergleich",
        "source": {
            "publisher": "World Bank", "title": "Gesamtfertilitätsrate im Ländervergleich",
            "url": "https://data.worldbank.org/indicator/SP.DYN.TFRT.IN",
            "dataset_code": "SP.DYN.TFRT.IN", "licence": "CC BY 4.0",
            "licence_url": "https://creativecommons.org/licenses/by/4.0/",
            "redistributable": True,
            "attribution": "Datenquelle: World Bank – data.worldbank.org (SP.DYN.TFRT.IN, CC BY 4.0)",
            "retrieved": retrieved, "stand": fstand,
        },
        "unit": "Kinder je Frau", "subjects": ["GWB", "MAT"],
        "keywords": ["Fertilität", "Fertilitätsrate", "Geburtenrate", "Kinderzahl",
                     "Bevölkerungsdynamik", "Demografie", "Ländervergleich", "global", "Daten"],
        "competences": [],
        "series": {"vergleich": {"label": "Gesamtfertilitätsrate (Kinder je Frau)",
                                 "categories": fcats, "values": fvals}},
    })
    return out


def build(retrieved: str) -> list[dict]:
    out = []
    for did, kind, country, indicator, title, unit, nd, subjects, keywords, comps in DATASETS:
        print(f"[fetch] {did}  ({indicator})")
        if kind == "series":
            cats, vals, stand = _series(country, indicator, nd)
            series = {"verlauf": {"label": title, "categories": cats, "values": vals}}
        else:
            cats, vals, stand = _compare(indicator, nd)
            series = {"vergleich": {"label": title, "categories": cats, "values": vals}}
        ind_url = f"https://data.worldbank.org/indicator/{indicator}"
        out.append({
            "id": did, "title": title,
            "source": {
                "publisher": "World Bank", "title": title, "url": ind_url,
                "dataset_code": indicator, "licence": "CC BY 4.0",
                "licence_url": "https://creativecommons.org/licenses/by/4.0/",
                "redistributable": True,
                "attribution": f"Datenquelle: World Bank – data.worldbank.org ({indicator}, CC BY 4.0)",
                "retrieved": retrieved, "stand": stand,
            },
            "unit": unit, "subjects": subjects, "keywords": keywords, "competences": comps,
            "series": series,
        })
        print(f"        {len(next(iter(series.values()))['categories'])} points, Stand {stand}")
    return out


def write(datasets: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cat_path = OUT_DIR / "_catalog.json"
    catalog = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"datasets": []}
    by_id = {d["id"]: d for d in catalog.get("datasets", [])}
    for ds in datasets:
        (OUT_DIR / f"{ds['id']}.json").write_text(
            json.dumps(ds, ensure_ascii=False, indent=2), encoding="utf-8")
        by_id[ds["id"]] = {"id": ds["id"], "title": ds["title"], "file": f"{ds['id']}.json",
                           "source": ds["source"], "series": list(ds["series"].keys())}
    catalog["datasets"] = sorted(by_id.values(), key=lambda d: d["id"])
    cat_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[write] {len(datasets)} datasets -> {OUT_DIR}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieved", default=_dt.date.today().isoformat())
    ap.add_argument("--extend", action="store_true",
                    help="additive: add urbanisation welt_verlauf + fertility only "
                         "(do NOT re-fetch the six curated datasets)")
    args = ap.parse_args()
    write(build_extension(args.retrieved) if args.extend else build(args.retrieved))


if __name__ == "__main__":
    main()
