"""Fetch district-level Austrian population from official Statistik Austria OGD.

Population rows come from ``OGD_bevstandjbab2002_BevStand_2024``. Political
district names come from the matching official 2025 WFS boundary layer. The
first three digits of the five-digit municipality code are Statistik Austria's
political-district identifier. Vienna therefore remains 23 districts rather
than being collapsed into one Land.

Run:  python -m tools.fetch_statistik_austria_regional --retrieved 2026-07-11
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import urllib.request

from tools.fetch_statistik_austria import write

POP_DATASET = "OGD_bevstandjbab2002_BevStand_2024"
POP_URL = f"https://data.statistik.gv.at/data/{POP_DATASET}.csv"
LANDING = f"https://data.statistik.gv.at/web/meta.jsp?dataset={POP_DATASET}"
DISTRICT_WFS = (
    "https://www.statistik.gv.at/gs-open/GEODATA/ows?service=WFS&version=2.0.0"
    "&request=GetFeature&typeNames=GEODATA:STATISTIK_AUSTRIA_POLBEZ_20250101"
    "&outputFormat=application/json&srsName=EPSG:4326"
)
DATASET_ID = "statistik_austria_bezirke_2024"
COL_MUNICIPALITY = "C-GRGEMAKT-0"
COL_VALUE = "F-ISIS-1"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-OGD-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return response.read()


def district_names(boundary_json: str | bytes) -> dict[str, str]:
    raw = json.loads(boundary_json)
    names: dict[str, str] = {}
    for feature in raw.get("features", []):
        props = feature.get("properties", {})
        code, name = str(props.get("g_id", "")), str(props.get("g_name", ""))
        # WFS 2025 includes the whole-city Wien overlay (900) and the 23
        # Gemeindebezirke (901–923). Facts use the latter; skip the duplicate.
        if code and name and code != "900":
            names[code] = name
    if not names:
        raise ValueError("district boundary source contains no g_id/g_name pairs")
    return names


def parse_district_population(fact_csv: str, names: dict[str, str], retrieved: str) -> dict:
    totals = {code: 0 for code in names}
    for row in csv.DictReader(io.StringIO(fact_csv), delimiter=";"):
        if not row.get(COL_VALUE):
            continue
        municipality = row[COL_MUNICIPALITY].rsplit("-", 1)[-1]
        code = municipality[:3]
        if code not in totals:
            raise ValueError(f"population row has district code absent from WFS: {code}")
        totals[code] += int(row[COL_VALUE])
    if any(value <= 0 for value in totals.values()):
        missing = [code for code, value in totals.items() if value <= 0]
        raise ValueError(f"districts without population rows: {missing}")

    codes = sorted(totals)
    counts = [totals[code] for code in codes]
    total = sum(counts)
    return {
        "id": DATASET_ID,
        "title": "Bevölkerung der österreichischen politischen Bezirke (1.1.2024)",
        "source": {
            "publisher": "Statistik Austria",
            "title": "Bevölkerungsstand zu Jahresbeginn 2024 (nach politischem Bezirk aggregiert)",
            "url": LANDING,
            "dataset_code": POP_DATASET,
            "licence": "CC BY 4.0",
            "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.de",
            "redistributable": True,
            "attribution": "Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)",
            "retrieved": retrieved,
            "stand": "2024-01-01; Gebietsstand 2025",
        },
        "subjects": ["GWB", "MAT"],
        "keywords": ["Politische Bezirke", "Bezirk", "Bevölkerung", "Regionen", "Wien",
                     "Österreich", "Verteilung", "Karte"],
        "competences": ["GWB.US.3.OST.01"],
        "unit": "Personen",
        "totals": {"gesamt": total},
        "series": {
            "bevoelkerung": {
                "label": "Bevölkerung je politischem Bezirk",
                "kind": "choropleth",
                "geo_id": "at_bezirke_2025",
                "region_codes": codes,
                "groups": [names[code] for code in codes],
                "counts": counts,
                "shares_pct": [round(100 * value / total, 2) for value in counts],
            }
        },
    }


def fetch(retrieved: str) -> dict:
    names = district_names(_get(DISTRICT_WFS))
    facts = _get(POP_URL).decode("utf-8-sig")
    return parse_district_population(facts, names, retrieved)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieved", default=dt.date.today().isoformat())
    args = parser.parse_args()
    write([fetch(args.retrieved)])


if __name__ == "__main__":
    main()
