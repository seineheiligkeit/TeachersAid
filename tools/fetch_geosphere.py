"""Deterministic fetch of GeoSphere Austria climate normals → grounding/data/.

GeoSphere Austria's data hub (data.hub.geosphere.at, dataset `klima-v2-1m`) is CC BY 4.0.
We compute **climate normals** (1991–2020 monthly means of temperature and monthly-sum
precipitation) per station by deterministic averaging — no LLM in the fact path — to feed
the `climate_diagram` (Klimadiagramm) recipe. A few stations across climate regions
(lowland east, inner-alpine, west/lake) give contrastable Kernfragen.

    python tools/fetch_geosphere.py
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
API = "https://dataset.api.hub.geosphere.at/v1/station/historical/klima-v2-1m"

DATASET_ID = "geosphere_klima_normal_1991_2020"
START, END = "1991-01-01T00:00", "2020-12-01T00:00"
MONTHS = ["Jän", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

# slug -> (station_id, display name)
STATIONS = {
    "wien": (105, "Wien (Hohe Warte)"),
    "innsbruck": (39, "Innsbruck (Universität)"),
    "bregenz": (15, "Bregenz"),
    "graz": (30, "Graz (Universität)"),
}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-GSA-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8")


def _normals(station_id: int) -> tuple[list[float], list[float]]:
    """Monthly normals (1991–2020): mean temperature and mean monthly precipitation sum."""
    url = (f"{API}?parameters=tl_mittel,rr&start={START}&end={END}"
           f"&station_ids={station_id}&output_format=csv")
    rows = list(csv.DictReader(io.StringIO(_get(url))))
    t_sum = [0.0] * 12
    t_n = [0] * 12
    p_sum = [0.0] * 12
    p_n = [0] * 12
    for r in rows:
        m = int(r["time"][5:7]) - 1
        if r.get("tl_mittel"):
            t_sum[m] += float(r["tl_mittel"])
            t_n[m] += 1
        if r.get("rr"):
            p_sum[m] += float(r["rr"])
            p_n[m] += 1
    temp = [round(t_sum[i] / t_n[i], 1) if t_n[i] else None for i in range(12)]
    precip = [round(p_sum[i] / p_n[i]) if p_n[i] else None for i in range(12)]
    return temp, precip


def build(retrieved: str) -> dict:
    print(f"[fetch] {DATASET_ID} (GeoSphere Austria, CC BY 4.0)")
    series = {}
    for slug, (sid, name) in STATIONS.items():
        temp, precip = _normals(sid)
        series[slug] = {"label": name, "kind": "climate_diagram",
                        "months": MONTHS, "temp": temp, "precip": precip}
        print(f"        {name}: Ø {sum(t for t in temp if t is not None) / 12:.1f}°C, "
              f"{sum(p for p in precip if p is not None):.0f} mm/Jahr")
    return {
        "id": DATASET_ID,
        "title": "Klimanormalwerte österreichischer Stationen (1991–2020)",
        "source": {
            "publisher": "GeoSphere Austria",
            "title": "Monatsdaten Klima (klima-v2-1m), Normalperiode 1991–2020",
            "url": "https://data.hub.geosphere.at/dataset/klima-v2-1m",
            "dataset_code": "klima-v2-1m", "licence": "CC BY 4.0",
            "licence_url": "https://creativecommons.org/licenses/by/4.0/",
            "redistributable": True,
            "attribution": "Datenquelle: GeoSphere Austria – data.hub.geosphere.at (klima-v2-1m, CC BY 4.0)",
            "retrieved": retrieved, "stand": "1991–2020",
        },
        "unit": "°C / mm",
        "subjects": ["GWB"],
        "keywords": ["Klima", "Klimadiagramm", "Temperatur", "Niederschlag", "Wetter",
                     "Jahreszeiten", "Wien", "Innsbruck", "Bregenz", "Graz", "Alpen"],
        "competences": [],
        "series": series,
    }


def write(dataset: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{DATASET_ID}.json").write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    cat_path = OUT_DIR / "_catalog.json"
    catalog = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"datasets": []}
    by_id = {d["id"]: d for d in catalog.get("datasets", [])}
    by_id[dataset["id"]] = {"id": dataset["id"], "title": dataset["title"],
                            "file": f"{DATASET_ID}.json", "source": dataset["source"],
                            "series": list(dataset["series"].keys())}
    catalog["datasets"] = sorted(by_id.values(), key=lambda d: d["id"])
    cat_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[write] {OUT_DIR / (DATASET_ID + '.json')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retrieved", default=_dt.date.today().isoformat())
    args = ap.parse_args()
    write(build(args.retrieved))


if __name__ == "__main__":
    main()
