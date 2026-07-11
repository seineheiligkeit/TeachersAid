"""Deterministic fetch of the Nationalratswahl 2024 result → grounding/data/.

The Austrian Interior Ministry (BMI) publishes the official result of the 2024
Nationalratswahl on data.gv.at under **CC BY 4.0** (redistribution permitted with
attribution). The main result file is a semicolon-separated, cp1252-encoded CSV whose
first column is the Gebietskennziffer (``G00000`` = Österreich, ``G<N>0000`` = the nine
Bundesländer) and whose party columns carry the *gültige Stimmen* per party. No LLM in
the fact path — the file is fetched, parsed, licence-checked and written with its citation.

Licence discipline (``verify_licence``): the tool asserts the dataset metadata advertises
CC BY 4.0 before writing; it **fails closed** if the licence is missing or different. The
licence was verified against the portal at build time (Creative Commons Attribution 4.0,
https://creativecommons.org/licenses/by/4.0/, publisher BMI).

The official *Mandatsverteilung* (57/51/41/18/16) is NOT in the votes CSV; it is recorded
here as a curated, cited fact from the BMI endgültiges Ergebnis (a real published number,
selected — never computed-and-presented-as-official; the d'Hondt engine's computed seats
are always shown as a *simplification*, see pipeline/wahl.py).

    python tools/fetch_nrw_results.py            # fetch + write the dataset
    python tools/fetch_nrw_results.py --offline  # re-derive from a cached CSV (no network)
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import json
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "teachersaid" / "grounding" / "data"
DATASET_ID = "bmi_nrw_2024"

# --- data.gv.at resources (verified 2026-07-11) --------------------------------------
DATASET_PAGE = "https://www.data.gv.at/katalog/dataset/e40e3b00-1a98-4338-acb7-42547e6fee55"
META_API = "https://www.data.gv.at/api/hub/repo/datasets/e40e3b00-1a98-4338-acb7-42547e6fee55"
RESULT_CSV = (
    "https://www.data.gv.at/katalog/dataset/e40e3b00-1a98-4338-acb7-42547e6fee55/"
    "resource/ce85ad5c-e471-42c0-83e5-580dbb627717/download/wahl_20241003_214746.csv"
)
CSV_ENCODING = "cp1252"

# The party columns of the BMI result file, in ballot order. Only the five parties that
# cleared the 4 % Sperrklausel entered the Nationalrat; the rest are kept for the honest
# "why the threshold matters" task (running d'Hondt on ALL parties gives KPÖ/BIER seats).
PARTIES = ["ÖVP", "SPÖ", "FPÖ", "GRÜNE", "NEOS", "BIER", "MFG", "BGE", "LMP", "GAZA",
           "KPÖ", "KEINE"]
NR_PARTIES = ["FPÖ", "ÖVP", "SPÖ", "NEOS", "GRÜNE"]  # ≥ 4 % → seats

# GKZ → Bundesland (the aggregate rows; the file also carries Wahlkarten- and
# Regionalwahlkreis rows we deliberately skip — the G<N>0000 rows are the Land totals).
BUNDESLAND_GKZ = {
    "G00000": "Österreich",
    "G10000": "Burgenland", "G20000": "Kärnten", "G30000": "Niederösterreich",
    "G40000": "Oberösterreich", "G50000": "Salzburg", "G60000": "Steiermark",
    "G70000": "Tirol", "G80000": "Vorarlberg", "G90000": "Wien",
}


def _slug(name: str) -> str:
    return (name.lower().replace("ä", "ae").replace("ö", "oe")
            .replace("ü", "ue").replace("ß", "ss"))


# stable key per region for the dataset's `series` dict
SERIES_KEY = {name: ("bund" if gkz == "G00000" else "bl_" + _slug(name))
              for gkz, name in BUNDESLAND_GKZ.items()}

# The official Mandatsverteilung of the 2024 Nationalrat — a curated, cited BMI fact (the
# votes CSV carries no seats). Recorded here so the coalition task rests on the REAL result,
# never on our simplified d'Hondt. Source: BMI, endgültiges Ergebnis der NRW 2024.
MANDATE_AMTLICH_2024 = {"FPÖ": 57, "ÖVP": 51, "SPÖ": 41, "NEOS": 18, "GRÜNE": 16}
MANDATE_GESAMT = 183
MEHRHEIT = MANDATE_GESAMT // 2 + 1  # 92
SPERRKLAUSEL_PROZENT = 4

LICENCE = "CC BY 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by/4.0/"
ATTRIBUTION = ("Datenquelle: Bundesministerium für Inneres (BMI) – data.gv.at "
               "(Ergebnisse der Nationalratswahl 2024, CC BY 4.0)")
STAND = "2024-10-03 (endgültiges Ergebnis inkl. Wahlkarten)"


def _num(cell: str | None) -> int:
    """A vote cell → int; empty (party not standing in a region) → 0."""
    s = (cell or "").strip().replace(".", "").replace(" ", "")
    return int(s) if s else 0


# --- pure parse helpers (offline-testable: take already-fetched CSV text) --------------
def parse_wahl_csv(text: str) -> dict[str, dict]:
    """A BMI NRW result CSV (semicolon, cp1252-decoded text) → {region_name: record}.

    Each record is ``{"gkz", "gueltige", "votes": {party: int}}`` for Österreich and the
    nine Bundesländer (the G<N>0000 aggregate rows). Deterministic; no network."""
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    header = rows[0]
    gi = header.index("Gültige")
    pidx = {p: header.index(p) for p in PARTIES if p in header}
    by_gkz = {r[0]: r for r in rows[1:] if r}
    out: dict[str, dict] = {}
    for gkz, name in BUNDESLAND_GKZ.items():
        r = by_gkz.get(gkz)
        if r is None:
            continue
        out[name] = {
            "gkz": gkz,
            "gueltige": _num(r[gi]),
            "votes": {p: _num(r[pidx[p]]) for p in pidx},
        }
    return out


def verify_licence(meta: dict) -> bool:
    """True iff the dataset metadata advertises CC BY 4.0 (fail-closed otherwise).

    Scans the metadata blob for the CC-BY-4.0 URL or the 'Attribution 4.0' name — robust
    to the exact DCAT/JSON shape data.gv.at returns."""
    blob = json.dumps(meta, ensure_ascii=False).lower()
    return ("creativecommons.org/licenses/by/4.0" in blob
            or "attribution 4.0" in blob
            or "cc by 4.0" in blob or "cc-by-4.0" in blob)


# display series: only parties ≥ this share of the valid votes → a legible bar chart (the
# full 12-party `bund` series keeps the tiny parties for the "d'Hondt on ALL parties" task).
HAUPT_MIN_PROZENT = 2.0


def build_dataset(parsed: dict[str, dict], *, retrieved: str) -> dict:
    """Assemble the curated dataset record from parsed regions. `bund` first."""
    series: dict[str, dict] = {}
    for gkz, name in BUNDESLAND_GKZ.items():
        rec = parsed.get(name)
        if rec is None:
            continue
        series[SERIES_KEY[name]] = {
            "label": ("Österreich gesamt" if gkz == "G00000"
                      else f"{name} (gültige Stimmen)"),
            "categories": list(PARTIES),
            "values": [rec["votes"].get(p, 0) for p in PARTIES],
            "gueltige": rec["gueltige"],
        }
    # a legible display slice: the parties above 2 % (the 5 that entered the Nationalrat plus
    # the two that just missed the 4-%-Hürde — exactly the ones the reading task is about)
    bund_rec = parsed.get("Österreich")
    if bund_rec is not None:
        g = bund_rec["gueltige"]
        haupt = [p for p in PARTIES if bund_rec["votes"].get(p, 0) >= HAUPT_MIN_PROZENT / 100 * g]
        series["bund_hauptparteien"] = {
            "label": "Gültige Stimmen (Parteien über 2 %)",
            "categories": haupt,
            "values": [bund_rec["votes"][p] for p in haupt],
            "gueltige": g,
        }
    return {
        "id": DATASET_ID,
        "title": "Nationalratswahl 2024 – gültige Stimmen nach Partei (Bund und Bundesländer)",
        "source": {
            "publisher": "Bundesministerium für Inneres (BMI)",
            "title": "Ergebnisse der Nationalratswahl 2024",
            "url": DATASET_PAGE,
            "dataset_code": "e40e3b00-1a98-4338-acb7-42547e6fee55",
            "licence": LICENCE, "licence_url": LICENCE_URL,
            "redistributable": True, "attribution": ATTRIBUTION,
            "retrieved": retrieved, "stand": STAND,
        },
        "unit": "Stimmen",
        "subjects": ["GPB", "GWB", "MAT"],
        "keywords": ["Wahl", "Wahlen", "Nationalratswahl", "Mandate", "Mandatsverteilung",
                     "D'Hondt", "Verhältniswahl", "Demokratie", "Parteien", "Stimmen",
                     "Koalition", "Politik", "Wählen", "Daten"],
        "competences": ["GPB.US.4.ALL.07", "GPB.US.4.ALL.09", "GPB.US.4.ALL.10"],
        # curated aggregate facts (Mandate are the official BMI result, not in the votes file)
        "totals": {
            "mandate_gesamt": MANDATE_GESAMT,
            "mehrheit": MEHRHEIT,
            "sperrklausel_prozent": SPERRKLAUSEL_PROZENT,
            "nr_parteien": list(NR_PARTIES),
            "mandate_amtlich": dict(MANDATE_AMTLICH_2024),
            "mandate_quelle": "BMI, endgültiges Ergebnis der Nationalratswahl 2024",
        },
        "series": series,
    }


# --- network + write -------------------------------------------------------------------
def _get(url: str, *, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-NRW-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
    return raw if binary else raw.decode("utf-8")


def fetch(*, retrieved: str, cache_csv: Path | None = None) -> dict:
    """Fetch + licence-check + parse + build. `cache_csv` (if it exists) is used instead
    of the network so a re-run is reproducible offline."""
    try:
        meta = json.loads(_get(META_API))
        if not verify_licence(meta):
            raise SystemExit(
                "LICENCE CHECK FAILED: data.gv.at metadata does not advertise CC BY 4.0 "
                "— refusing to redistribute (fail closed)."
            )
        print(f"[licence] verified {LICENCE} via {META_API}")
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — the flaky SPA API must not block a verified fetch
        print(f"[licence] metadata API unavailable ({type(exc).__name__}); using the "
              f"build-time-verified licence {LICENCE} ({LICENCE_URL})")

    if cache_csv and cache_csv.exists():
        text = cache_csv.read_bytes().decode(CSV_ENCODING)
        print(f"[fetch] using cached CSV {cache_csv}")
    else:
        text = _get(RESULT_CSV, binary=True).decode(CSV_ENCODING)
        if cache_csv:
            cache_csv.write_bytes(text.encode(CSV_ENCODING))
        print(f"[fetch] {RESULT_CSV}")
    parsed = parse_wahl_csv(text)
    bund = parsed["Österreich"]
    print(f"[parse] Bund: {bund['gueltige']} gültige, "
          f"{sum(bund['votes'].values())} Parteistimmen; {len(parsed)} Gebiete")
    return build_dataset(parsed, retrieved=retrieved)


def write(dataset: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{dataset['id']}.json").write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    cat_path = OUT_DIR / "_catalog.json"
    catalog = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"datasets": []}
    by_id = {d["id"]: d for d in catalog.get("datasets", [])}
    by_id[dataset["id"]] = {
        "id": dataset["id"], "title": dataset["title"], "file": f"{dataset['id']}.json",
        "source": dataset["source"], "series": list(dataset["series"].keys()),
    }
    catalog["datasets"] = sorted(by_id.values(), key=lambda d: d["id"])
    cat_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[write] {dataset['id']} ({len(dataset['series'])} series) -> {OUT_DIR}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieved", default=_dt.date.today().isoformat())
    ap.add_argument("--cache", default=None,
                    help="path to cache/read the raw CSV (offline re-run)")
    ap.add_argument("--offline", action="store_true",
                    help="require the cached CSV (no network for the votes file)")
    args = ap.parse_args()
    cache = Path(args.cache) if args.cache else (OUT_DIR / "_bmi_nrw2024_source.csv")
    if args.offline and not cache.exists():
        raise SystemExit(f"--offline: no cached CSV at {cache}")
    write(fetch(retrieved=args.retrieved, cache_csv=cache))


if __name__ == "__main__":
    main()
