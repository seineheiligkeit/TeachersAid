"""Deterministic fetch of NOAA Mauna Loa annual-mean CO₂ → grounding/data/.

The Keeling curve (atmospheric CO₂ measured at Mauna Loa) is the iconic climate
time-series. NOAA GML publishes it as a plain whitespace text file; NOAA data is a
**U.S. Government work → public domain** (freely reusable, citation requested), so it is
the cleanest possible source for the CO₂-concentration figure. No LLM in the fact path —
the file is fetched, parsed, and written with its citation, exactly like the World-Bank /
Statistik-Austria tools (the `parse_lehrplan` precedent).

    python tools/fetch_noaa_co2.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "teachersaid" / "grounding" / "data"
URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.txt"
DATASET_ID = "noaa_co2_mauna_loa"
# the decade grid the worksheet figure shows (a legible 8-point trend, not 60 rows)
DECADES = [1960, 1970, 1980, 1990, 2000, 2010, 2020, 2024]


def parse_annmean(text: str) -> dict[int, float]:
    """NOAA `co2_annmean_mlo.txt` → {year: mean_ppm}. Pure (offline-testable): skip the
    `#`-comment header, read the first two whitespace columns (year, mean)."""
    out: dict[int, float] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) >= 2:
            try:
                out[int(parts[0])] = float(parts[1])
            except ValueError:
                continue
    return out


def series_for_years(annual: dict[int, float], years: list[int]) -> tuple[list[str], list[float]]:
    """Project the annual means onto the figure's decade grid (1 decimal ppm)."""
    cats = [str(y) for y in years if y in annual]
    vals = [round(annual[y], 1) for y in years if y in annual]
    return cats, vals


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-NOAA-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def build(retrieved: str) -> list[dict]:
    print(f"[fetch] {DATASET_ID}  ({URL})")
    annual = parse_annmean(_get(URL))
    cats, vals = series_for_years(annual, DECADES)
    stand = cats[-1] if cats else ""
    print(f"        {len(cats)} points, {cats[0]}–{cats[-1]}, Stand {stand}")
    return [{
        "id": DATASET_ID,
        "title": "Atmosphärische CO₂-Konzentration (Mauna Loa, Jahresmittel)",
        "source": {
            "publisher": "NOAA Global Monitoring Laboratory (GML)",
            "title": "Trends in Atmospheric Carbon Dioxide — Mauna Loa annual mean (Keeling-Kurve)",
            "url": "https://gml.noaa.gov/ccgg/trends/",
            "dataset_code": "co2_annmean_mlo",
            "licence": "Public Domain (U.S. Government work)",
            "licence_url": "https://www.noaa.gov/information-technology/open-data-dissemination",
            "redistributable": True,
            "attribution": "Datenquelle: NOAA Global Monitoring Laboratory (GML) – "
                           "Mauna Loa CO₂ (Keeling-Kurve), gml.noaa.gov",
            "retrieved": retrieved, "stand": stand,
        },
        "unit": "ppm",
        "subjects": ["GWB", "PHY", "MAT"],
        "keywords": ["CO2", "Kohlendioxid", "Klima", "Klimawandel", "Treibhausgas",
                     "Atmosphäre", "Keeling", "Emissionen", "global", "Daten"],
        "competences": [],
        "series": {"verlauf": {"label": "CO₂-Konzentration (ppm)", "categories": cats, "values": vals}},
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
