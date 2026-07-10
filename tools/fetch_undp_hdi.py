"""Deterministic fetch of the UNDP Human Development Index → grounding/data/.

The HDI is the standard cross-country "Lebensqualität" composite. UNDP Human Development
Reports data (incl. the HDI time-series) is released under **CC BY 3.0 IGO** — verified on
hdr.undp.org/copyright-and-terms-use (share + adapt, attribution required) — so it is
redistributable with attribution, exactly like the World-Bank (CC BY 4.0) source. No LLM
in the fact path: the composite-indices CSV is fetched, the latest HDI column is parsed for
the requested countries, and the record is written with its citation.

    python tools/fetch_undp_hdi.py
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import json
import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "teachersaid" / "grounding" / "data"
# HDR 2025 release, composite indices complete time series (all countries × years).
URL = "https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv"
DATASET_ID = "undp_hdi"
# (ISO3, German display name), kept in the worksheet figure's low→high order.
COUNTRIES = [
    ("NER", "Niger"), ("AFG", "Afghanistan"), ("BOL", "Bolivien"), ("BRA", "Brasilien"),
    ("TUR", "Türkei"), ("AUT", "Österreich"), ("CHE", "Schweiz"), ("NOR", "Norwegen"),
]


def parse_hdi(csv_text: str, order: list[tuple[str, str]]) -> tuple[list[str], list[float], str]:
    """UNDP composite-indices CSV → (categories, HDI values, latest_year). Pure/offline-
    testable: pick the latest `hdi_<year>` VALUE column (never an `hdi_rank_<year>` column),
    read it for each requested ISO3, keep the given order. Missing values (`..`) are skipped."""
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        return [], [], ""
    years = sorted(int(m.group(1)) for c in rows[0] if (m := re.fullmatch(r"hdi_(\d{4})", c)))
    if not years:
        return [], [], ""
    col = f"hdi_{years[-1]}"
    by_iso = {r.get("iso3"): r for r in rows}
    cats: list[str] = []
    vals: list[float] = []
    for iso, name in order:
        r = by_iso.get(iso)
        raw = (r or {}).get(col)
        if raw not in (None, "", ".."):
            cats.append(name)
            vals.append(round(float(raw), 3))
    return cats, vals, str(years[-1])


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-UNDP-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8-sig", "replace")


def build(retrieved: str) -> list[dict]:
    print(f"[fetch] {DATASET_ID}  ({URL})")
    cats, vals, year = parse_hdi(_get(URL), COUNTRIES)
    print(f"        {len(cats)} countries, Stand {year}")
    return [{
        "id": DATASET_ID,
        "title": "Human Development Index (HDI) im Ländervergleich",
        "source": {
            "publisher": "UNDP Human Development Reports Office",
            "title": "Human Development Index — Composite indices complete time series (HDR 2025)",
            "url": "https://hdr.undp.org/data-center/human-development-index",
            "dataset_code": "HDR25_Composite_indices",
            "licence": "CC BY 3.0 IGO",
            "licence_url": "https://creativecommons.org/licenses/by/3.0/igo/",
            "redistributable": True,
            "attribution": "Datenquelle: UNDP Human Development Reports – hdr.undp.org "
                           "(HDI, CC BY 3.0 IGO)",
            "retrieved": retrieved, "stand": year,
        },
        "unit": "HDI (0–1)",
        "subjects": ["GWB"],
        "keywords": ["HDI", "Entwicklung", "Entwicklungsindex", "Lebensqualität", "Wohlstand",
                     "Lebenserwartung", "Bildung", "Disparitäten", "Ländervergleich", "global", "Daten"],
        "competences": [],
        "series": {"vergleich": {"label": "HDI (0–1)", "categories": cats, "values": vals}},
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
