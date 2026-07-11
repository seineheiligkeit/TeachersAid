"""Fetch a BIO-relevant Statistik Austria health series into grounding/data/.

The source is the official OGD table ``OGD_ind003_HVD_IND_1`` (CC BY 4.0).
We select remaining life expectancy at birth for Austria, by sex, for every
available year. Parsing is pure and fixture-tested; live retrieval is never
part of the test suite.

Run:  python -m tools.fetch_statistik_austria_health --retrieved 2026-07-11
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import urllib.request

from tools.fetch_statistik_austria import write

DATASET = "OGD_ind003_HVD_IND_1"
BASE = f"https://data.statistik.gv.at/data/{DATASET}"
LANDING = f"https://data.statistik.gv.at/web/meta.jsp?dataset={DATASET}"
DATASET_ID = "statistik_austria_lebenserwartung_2002_2024"

COL_YEAR = "C-DEMIND_ZEIT-0"
COL_REGION = "C-DEMIND_NUTS-0"
COL_AGE = "C-DEMIND_ALTER-0"
COL_SEX = "C-DEMIND_GESCHLECHT-0"
COL_VALUE = "F-DEMIND_LEBENSERWARTUNG-0"

AUSTRIA = "DEMIND_NUTS-0"
AGE_ZERO = "DEMIND_ALTER-0"
SEX = {
    "DEMIND_GESCHLECHT-1": "männlich",
    "DEMIND_GESCHLECHT-2": "weiblich",
}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-OGD-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8-sig")


def parse_life_expectancy(fact_csv: str, retrieved: str) -> dict:
    """Select Austria × age 0 × sex and return one cited Dataset record."""
    rows = csv.DictReader(io.StringIO(fact_csv), delimiter=";")
    values: dict[str, dict[int, float]] = {label: {} for label in SEX.values()}
    for row in rows:
        if row[COL_REGION] != AUSTRIA or row[COL_AGE] != AGE_ZERO:
            continue
        label = SEX.get(row[COL_SEX])
        if label is None or not row[COL_VALUE]:
            continue
        year = int(row[COL_YEAR].rsplit("-", 1)[-1])
        values[label][year] = float(row[COL_VALUE].replace(",", "."))

    years = sorted(set(values["männlich"]) & set(values["weiblich"]))
    if not years:
        raise ValueError("no complete Austria/age-0/sex life-expectancy observations")
    male = [values["männlich"][year] for year in years]
    female = [values["weiblich"][year] for year in years]
    stand = str(years[-1])
    source = {
        "publisher": "Statistik Austria",
        "title": "Fernere Lebenserwartung nach Alter für Österreich und NUTS-2-Regionen ab 2002",
        "url": LANDING,
        "dataset_code": DATASET,
        "licence": "CC BY 4.0",
        "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.de",
        "redistributable": True,
        "attribution": "Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)",
        "retrieved": retrieved,
        "stand": stand,
    }
    return {
        "id": DATASET_ID,
        "title": f"Lebenserwartung bei Geburt in Österreich ({years[0]}–{years[-1]})",
        "source": source,
        "subjects": ["BIO", "GWB", "MAT"],
        "keywords": ["Gesundheit", "Lebenserwartung", "Sterblichkeit", "Geschlecht",
                     "Zeitreihe", "Datenanalyse", "Österreich"],
        "competences": ["BIO.US.x.WIS.02", "BIO.US.x.ERK.04"],
        "unit": "Jahre",
        "series": {
            "lebenserwartung_maennlich": {
                "label": "Lebenserwartung bei Geburt – männlich",
                "years": years,
                "values": male,
            },
            "lebenserwartung_weiblich": {
                "label": "Lebenserwartung bei Geburt – weiblich",
                "years": years,
                "values": female,
            },
            "vergleich_aktuell": {
                "label": f"Lebenserwartung bei Geburt nach Geschlecht ({years[-1]})",
                "groups": ["männlich", "weiblich"],
                "values": [male[-1], female[-1]],
            },
        },
    }


def fetch(retrieved: str) -> dict:
    return parse_life_expectancy(_get(f"{BASE}.csv"), retrieved)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieved", default=dt.date.today().isoformat())
    args = parser.parse_args()
    write([fetch(args.retrieved)])


if __name__ == "__main__":
    main()
