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
}
COMPARE = ["AT", "DE", "CH", "IT", "US", "CN", "IN", "NG"]

# id, kind, indicator, title, unit, round, subjects, keywords, competences
DATASETS = [
    ("worldbank_at_bevoelkerung", "series", "AT", "SP.POP.TOTL",
     "Bevölkerung Österreichs im Zeitverlauf", "Personen", 0,
     ["GWB"], ["Bevölkerung", "Bevölkerungsentwicklung", "Wachstum", "Demografie", "Zeitreihe"],
     ["GWB.US.3.OST.01"]),
    ("worldbank_at_alterung", "series", "AT", "SP.POP.65UP.TO.ZS",
     "Anteil der über 65-Jährigen in Österreich", "%", 1,
     ["GWB"], ["Alterung", "Überalterung", "Demografie", "Pensionen", "Altersstruktur", "65"],
     ["GWB.US.3.OST.01"]),
    ("worldbank_urbanisierung", "compare", None, "SP.URB.TOTL.IN.ZS",
     "Verstädterung im Ländervergleich (Anteil Stadtbevölkerung)", "%", 1,
     ["GWB"], ["Verstädterung", "Urbanisierung", "Stadt", "Land", "Disparitäten", "global"],
     []),
    ("worldbank_bip_pro_kopf", "compare", None, "NY.GDP.PCAP.CD",
     "BIP pro Kopf im Ländervergleich", "US-Dollar", 0,
     ["GWB"], ["BIP", "Wirtschaft", "Wohlstand", "Einkommen", "Disparitäten", "Ländervergleich", "global"],
     []),
    ("worldbank_co2_pro_kopf", "compare", None, "EN.GHG.CO2.PC.CE.AR5",
     "CO₂-Ausstoß pro Kopf im Ländervergleich", "t CO₂/Kopf", 1,
     ["GWB"], ["CO2", "Klima", "Klimawandel", "Emissionen", "Umwelt", "Disparitäten", "global"],
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
    args = ap.parse_args()
    write(build(args.retrieved))


if __name__ == "__main__":
    main()
