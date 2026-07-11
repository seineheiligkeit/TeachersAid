"""Deterministic fetch+parse of the Statistik Austria VPI long series → grounding/data/.

The grounded-facts analogue of `tools/fetch_statistik_austria.py`, for the
**Verbraucherpreisindex (VPI)** — the price index the Finanzführerschein's inflation
recipe computes from (`pipeline/finanz.py::inflation_vpi`). The rule the whole data layer
rests on — *select, never author* — holds here: the index numbers come from a tool
fetching + parsing a real, openly-licensed source, never from a model.

Source: Statistik Austria OGD portal `data.statistik.gv.at`, dataset
`OGD_vpi66_VPI_1966_1` — "Verbraucherpreisindex Basis 1966", licensed **CC BY 4.0**
(redistribution permitted with attribution). Star schema: a fact CSV
(`C-VPIZR-0` time period ; `C-VPI1-0` index classification ; `F-VPIMZBM` index value) plus
classification CSVs. The time dimension carries BOTH monthly codes (`VPIZR-YYYYMM`) and the
**annual-average** codes (`VPIZR-YYYY`, four digits only) — we curate the annual Gesamtindex
(`VPI-0`) series, which reaches back to 1967, so "was 1995 kostete …" is a real, cited fact.

The base-1966 series is the longest one Statistik Austria continues to publish, so a single
dataset spans a whole generation of inflation (ideal for the classroom). The base year is
arbitrary for the recipe — it computes price ratios idx(now)/idx(then), which are
base-independent.

Re-run for a new Stand (yearly): the annual value for the latest year appears once the
Jahresdurchschnitt is published; just run again (idempotent). Offline: the parser
(`parse_annual_index`) is fixture-tested in `tests/test_fetch_statistik_austria_vpi.py`.

    python -m tools.fetch_statistik_austria_vpi                 # fetch live, write grounding/data/
    python -m tools.fetch_statistik_austria_vpi --retrieved 2026-07-11
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

DATASET = "OGD_vpi66_VPI_1966_1"
BASE = f"https://data.statistik.gv.at/data/{DATASET}"
LANDING = f"https://data.statistik.gv.at/web/meta.jsp?dataset={DATASET}"

DATASET_ID = "statistik_austria_vpi"
BASIS = "1966=100"

# fact-CSV columns (semicolon-delimited)
COL_ZR, COL_IDX, COL_VAL = "C-VPIZR-0", "C-VPI1-0", "F-VPIMZBM"
GESAMTINDEX = "VPI-0"                       # "Gesamtindex (nach COICOP)"
_ANNUAL = re.compile(r"^VPIZR-(\d{4})$")   # annual average: no month suffix


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-OGD-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8-sig")


def _de_float(s: str) -> float:
    """A Statistik-Austria value like '350,20000' → 350.2 (German comma → dot)."""
    return float(s.strip().replace(".", "").replace(",", "."))


def parse_annual_index(main_csv: str) -> dict[int, float]:
    """The fact CSV → {year: Gesamtindex Jahresdurchschnitt}. Deterministic + offline-
    testable: filters the time dimension to the four-digit annual-average codes and the
    index classification to the Gesamtindex (`VPI-0`). Raises on an empty result (a schema
    change should fail loudly, not silently ship an empty series)."""
    rows = list(csv.reader(io.StringIO(main_csv), delimiter=";"))
    header = rows[0]
    iz, ii, iv = header.index(COL_ZR), header.index(COL_IDX), header.index(COL_VAL)
    out: dict[int, float] = {}
    for r in rows[1:]:
        if len(r) <= iv or not r[iv]:
            continue
        m = _ANNUAL.match(r[iz])
        if m and r[ii] == GESAMTINDEX:
            out[int(m.group(1))] = _de_float(r[iv])
    if not out:
        raise SystemExit("VPI parse produced no annual Gesamtindex values — schema changed?")
    return out


def fetch(retrieved: str) -> list[dict]:
    print(f"[fetch] {DATASET} (Statistik Austria OGD, CC BY 4.0)")
    annual = parse_annual_index(_get(f"{BASE}.csv"))
    years = sorted(annual)
    index = [round(annual[y], 1) for y in years]
    print(f"[fetch] Jahres-Gesamtindex {years[0]}…{years[-1]}  (n={len(years)}, Basis {BASIS})")

    source = {
        "publisher": "Statistik Austria",
        "title": "Verbraucherpreisindex (VPI), Basis 1966 = 100",
        "url": LANDING,
        "dataset_code": DATASET,
        "licence": "CC BY 4.0",
        "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.de",
        "redistributable": True,
        "attribution": "Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)",
        "retrieved": retrieved,
        "stand": f"Jahresdurchschnitt {years[-1]}",
    }
    dataset = {
        "id": DATASET_ID,
        "title": "Verbraucherpreisindex Österreich im Jahresdurchschnitt (Basis 1966 = 100)",
        "source": source,
        "subjects": ["GWB", "MAT"],
        "keywords": ["Inflation", "Verbraucherpreisindex", "VPI", "Preise", "Teuerung",
                     "Kaufkraft", "Preissteigerung", "Geldwert", "Lebenshaltungskosten"],
        "competences": ["GWB.US.3.ENT.09"],
        "unit": "Indexpunkte (Basis 1966 = 100)",
        "totals": {"basisjahr": 1966, "erstes_jahr": years[0], "letztes_jahr": years[-1]},
        "series": {
            "jahresindex": {
                "label": "Verbraucherpreisindex im Jahresdurchschnitt (Gesamtindex, Basis 1966 = 100)",
                "kind": "line",
                "basis": BASIS,
                "years": years,
                "index": index,
                # line-generator-compatible aliases (categories/values), so a figure could
                # be built from this series later without touching the recipe.
                "categories": years,
                "values": index,
            },
        },
    }
    return [dataset]


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
        print(f"[write] {OUT_DIR / (ds['id'] + '.json')}")
    catalog["datasets"] = sorted(by_id.values(), key=lambda d: d["id"])
    cat_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieved", default=_dt.date.today().isoformat(),
                    help="retrieval date (default: today)")
    args = ap.parse_args()
    write(fetch(args.retrieved))


if __name__ == "__main__":
    main()
