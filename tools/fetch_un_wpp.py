"""Deterministic fetch of continent populations from the UN World Population Prospects.

The authoritative source for population *by continent* (the World-Bank aggregates are the
7 WB regions, not continents; the UN Data Portal's data endpoint now requires a token).
UN DESA WPP is released under **CC BY 3.0 IGO** — redistributable with attribution, like
the UNDP HDI source. No LLM in the fact path: the standard `TotalPopulationBySex` CSV is
fetched, filtered to the Medium-variant continent rows for the target year, and written
with its citation. The 17 MB download is a one-time curation cost; the committed record
holds only the 6 continent totals.

    python tools/fetch_un_wpp.py
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import gzip
import io
import json
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "teachersaid" / "grounding" / "data"
URL = ("https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/"
       "CSV_FILES/WPP2024_TotalPopulationBySex.csv.gz")
DATASET_ID = "un_wpp_kontinente_2024"
YEAR = "2024"
VARIANT = "Medium"
# UN M49 aggregate LocIDs → German continent names, in the worksheet figure's order.
CONTINENTS = [
    (903, "Afrika"), (935, "Asien"), (908, "Europa"),
    (904, "Lat.Amerika"), (905, "Nordamerika"), (909, "Ozeanien"),
]


def parse_wpp(csv_text: str, continents: list[tuple[int, str]],
              year: str = YEAR, variant: str = VARIANT) -> tuple[list[str], list[float]]:
    """WPP `TotalPopulationBySex` CSV → (categories, population in billions). Pure/offline-
    testable: keep the one Medium-variant row per continent LocID for the target year;
    `PopTotal` is in thousands, so ÷1e6 → billions (rounded to 2 decimals, as the figure)."""
    by_loc: dict[int, str] = {}
    for row in csv.DictReader(io.StringIO(csv_text)):
        try:
            locid = int(row["LocID"])
        except (KeyError, ValueError, TypeError):
            continue
        if row.get("Time") == year and row.get("Variant") == variant and locid not in by_loc:
            by_loc[locid] = row.get("PopTotal", "")
    cats: list[str] = []
    vals: list[float] = []
    for locid, name in continents:
        raw = by_loc.get(locid)
        if raw not in (None, ""):
            cats.append(name)
            vals.append(round(float(raw) / 1e6, 2))
    return cats, vals


def _get_gz(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-UNWPP-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read()
    return gzip.decompress(raw).decode("utf-8-sig", "replace")


def build(retrieved: str) -> list[dict]:
    print(f"[fetch] {DATASET_ID}  ({URL.split('/')[-1]})")
    cats, vals = parse_wpp(_get_gz(URL), CONTINENTS)
    print(f"        {len(cats)} continents: " + ", ".join(f"{c} {v}" for c, v in zip(cats, vals)))
    return [{
        "id": DATASET_ID,
        "title": f"Weltbevölkerung nach Kontinenten ({YEAR})",
        "source": {
            "publisher": "United Nations, DESA, Population Division",
            "title": "World Population Prospects 2024 — Total Population by Sex (Medium variant)",
            "url": "https://population.un.org/wpp/",
            "dataset_code": "WPP2024_TotalPopulationBySex",
            "licence": "CC BY 3.0 IGO",
            "licence_url": "https://creativecommons.org/licenses/by/3.0/igo/",
            "redistributable": True,
            "attribution": "Datenquelle: United Nations, DESA, Population Division – "
                           "World Population Prospects 2024 (CC BY 3.0 IGO)",
            "retrieved": retrieved, "stand": YEAR,
        },
        "unit": "Mrd. Personen",
        "subjects": ["GWB", "MAT"],
        "keywords": ["Weltbevölkerung", "Kontinente", "Bevölkerung", "Bevölkerungsverteilung",
                     "Demografie", "Bevölkerungsdynamik", "global", "Daten"],
        "competences": [],
        "series": {"kontinente": {"label": "Bevölkerung in Milliarden",
                                  "categories": cats, "values": vals}},
    }]


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
    print(f"[write] {len(datasets)} dataset(s) -> {OUT_DIR}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieved", default=_dt.date.today().isoformat())
    args = ap.parse_args()
    write(build(args.retrieved))


if __name__ == "__main__":
    main()
