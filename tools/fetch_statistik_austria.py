"""Deterministic fetch+parse of a Statistik Austria OGD dataset → grounding/data/.

The grounded-facts analogue of `tools/parse_lehrplan.py`: a small, **LLM-free**
fetch+parse tool that turns a real, openly-licensed public dataset into a curated,
provenance-stamped JSON the engine can reference. The rule the whole data layer
rests on — *select, never author* — lives here: numbers come from a tool fetching
and parsing a real source, never from a model.

Source: Statistik Austria OGD portal `data.statistik.gv.at`, dataset
`OGD_bevstandjbab2002_BevStand_2024` — "Bevölkerungsstand zu Jahresbeginn 2024",
licensed **CC BY 4.0** (redistribution permitted with attribution). It is a star
schema: a fact CSV (count per year × sex × Gemeinde × single-year age) plus
classification CSVs that label the dimension codes.

What we curate from it (aggregated to the national total over all Gemeinden):
* `pyramide_5j` — population by 5-year age band × sex (the Bevölkerungspyramide);
* `altersgruppen_breit` — population by broad age group (0–14 … 75+), counts + shares.

Re-run for a new Stand: bump DATASET / STAND and run again; output is deterministic
for a given source file (only the retrieval date varies — pass --retrieved to pin it).

    python -m tools.fetch_statistik_austria            # fetch live, write grounding/data/
    python -m tools.fetch_statistik_austria --retrieved 2026-06-27
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

DATASET = "OGD_bevstandjbab2002_BevStand_2024"
BASE = f"https://data.statistik.gv.at/data/{DATASET}"
META_URL = f"https://data.statistik.gv.at/ogd/json?dataset={DATASET}"
LANDING = f"https://data.statistik.gv.at/web/meta.jsp?dataset={DATASET}"

DATASET_ID = "statistik_austria_bevstand_2024"
STAND = "2024-01-01"  # "zu Jahresbeginn 2024"

# main fact CSV columns (semicolon-delimited): year ; sex ; Gemeinde ; age ; count
COL_SEX, COL_AGE, COL_GEM, COL_VAL = "C-C11-0", "C-GALTEJ112-0", "C-GRGEMAKT-0", "F-ISIS-1"
SEX = {"C11-1": "male", "C11-2": "female"}

# the leading digit of the Gemeindekennziffer (GRGEMAKT-<5 digits>) is the Bundesland
BUNDESLAND = {
    "1": "Burgenland", "2": "Kärnten", "3": "Niederösterreich", "4": "Oberösterreich",
    "5": "Salzburg", "6": "Steiermark", "7": "Tirol", "8": "Vorarlberg", "9": "Wien",
}
BL_ID = "statistik_austria_bundeslaender_2024"


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-OGD-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8-sig")


def _rows(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text), delimiter=";"))


def _age_map(age_csv: str) -> dict[str, int]:
    """code → integer age, from the classification labels ("0 Jahre" … "100 Jahre
    und älter"). The 100+ band carries a different code prefix (GALT5J100-21)."""
    out: dict[str, int] = {}
    for row in _rows(age_csv)[1:]:
        if len(row) < 2 or not row[0]:
            continue
        m = re.match(r"\s*(\d+)", row[1])
        if m:
            out[row[0]] = int(m.group(1))
    return out


def _band5(age: int) -> int:
    """5-year band index: 0→[0-4] … 16→[80-84], 17→[85+] (open top)."""
    return min(age // 5, 17)


_BAND5_LABELS = [f"{i * 5}–{i * 5 + 4}" for i in range(17)] + ["85+"]

# broad groups used by the existing GWB demographics worksheet (c0094)
_BROAD = [
    ("0–14", range(0, 15)), ("15–29", range(15, 30)),
    ("30–44", range(30, 45)), ("45–59", range(45, 60)),
    ("60–74", range(60, 75)), ("75+", range(75, 201)),
]


def fetch(retrieved: str) -> list[dict]:
    print(f"[fetch] {DATASET} (Statistik Austria OGD, CC BY 4.0)")
    age = _age_map(_get(f"{BASE}_C-GALTEJ112-0.csv"))
    rows = _rows(_get(f"{BASE}.csv"))
    header = rows[0]
    ix_sex, ix_age, ix_val = header.index(COL_SEX), header.index(COL_AGE), header.index(COL_VAL)
    ix_gem = header.index(COL_GEM)

    # aggregate national totals over all Gemeinden → counts by (sex, single-year age),
    # and (from the same pass) population per Bundesland via the Gemeindekennziffer
    by_sex_age: dict[tuple[str, int], int] = {}
    bund: dict[str, int] = {b: 0 for b in BUNDESLAND.values()}
    for r in rows[1:]:
        if len(r) <= ix_val or not r[ix_val]:
            continue
        sex = SEX.get(r[ix_sex])
        a = age.get(r[ix_age])
        if sex is None or a is None:
            raise SystemExit(f"unmapped code in data row: sex={r[ix_sex]} age={r[ix_age]}")
        v = int(r[ix_val])
        by_sex_age[(sex, a)] = by_sex_age.get((sex, a), 0) + v
        digit = r[ix_gem].split("-")[-1][:1]   # GRGEMAKT-90001 → "9" → Wien
        if digit in BUNDESLAND:
            bund[BUNDESLAND[digit]] += v

    male5 = [0] * 18
    female5 = [0] * 18
    broad = {lbl: 0 for lbl, _ in _BROAD}
    for (sex, a), v in by_sex_age.items():
        (male5 if sex == "male" else female5)[_band5(a)] += v
        for lbl, rng in _BROAD:
            if a in rng:
                broad[lbl] += v
                break

    total_m, total_f = sum(male5), sum(female5)
    total = total_m + total_f
    print(f"[fetch] total={total:,}  male={total_m:,}  female={total_f:,}")

    source = {
        "publisher": "Statistik Austria",
        "title": "Bevölkerungsstand zu Jahresbeginn 2024",
        "url": LANDING,
        "dataset_code": DATASET,
        "licence": "CC BY 4.0",
        "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.de",
        "redistributable": True,
        "attribution": "Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)",
        "retrieved": retrieved,
        "stand": STAND,
    }
    broad_counts = [broad[lbl] for lbl, _ in _BROAD]
    dataset = {
        "id": DATASET_ID,
        "title": "Bevölkerung Österreichs nach Alter und Geschlecht (1.1.2024)",
        "source": source,
        # discovery metadata (curated tags so ideation can find this data by topic) —
        "subjects": ["GWB", "MAT"],
        "keywords": ["Bevölkerung", "Bevölkerungspyramide", "Demografie", "Altersstruktur",
                     "Alter", "Geschlecht", "Alterung", "Gesellschaft", "Pensionen"],
        "competences": ["GWB.US.3.OST.01"],
        "unit": "Personen",
        "totals": {"gesamt": total, "männlich": total_m, "weiblich": total_f},
        "series": {
            "pyramide_5j": {
                "label": "Bevölkerung nach 5-Jahres-Altersgruppen und Geschlecht",
                "kind": "population_pyramid",
                "age_groups": _BAND5_LABELS,
                "male": male5,
                "female": female5,
            },
            "altersgruppen_breit": {
                "label": "Bevölkerung nach breiten Altersgruppen",
                "groups": [lbl for lbl, _ in _BROAD],
                "counts": broad_counts,
                "shares_pct": [round(100 * c / total, 1) for c in broad_counts],
            },
        },
    }
    bl_names = list(BUNDESLAND.values())
    bl_counts = [bund[b] for b in bl_names]
    bl_dataset = {
        "id": BL_ID,
        "title": "Bevölkerung der österreichischen Bundesländer (1.1.2024)",
        "source": {**source,
                   "title": "Bevölkerungsstand zu Jahresbeginn 2024 (nach Bundesland aggregiert)"},
        "subjects": ["GWB", "MAT"],
        "keywords": ["Bundesländer", "Bundesland", "Regionen", "regional", "Wien",
                     "Bevölkerung", "Verteilung", "Österreich", "Daten"],
        "competences": ["GWB.US.3.OST.01"],
        "unit": "Personen",
        "totals": {"gesamt": total},
        "series": {
            "bevoelkerung": {
                "label": "Bevölkerung je Bundesland",
                "groups": bl_names,
                "counts": bl_counts,
                "shares_pct": [round(100 * c / total, 1) for c in bl_counts],
            },
        },
    }
    return [dataset, bl_dataset]


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
