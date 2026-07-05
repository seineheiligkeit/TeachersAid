"""Fetch curated geographic BOUNDARY data — the map-figure fact set.

The spatial analogue of the grounded-facts data layer: a map's boundaries are FACTS, so they
are fetched deterministically from a clearly-licensed source and stored as a curated, cited
geographic dataset — never authored. The choropleth recipe (`matplotlib:choropleth_map`) reads
these polygons; content references a boundary set by stable `geo_id`, exactly as a figure
references a `Dataset`. *Select, never author* — applied to geography.

Licence-gated: we only redistribute boundary geometry under a recorded redistributable licence
(CC BY / PD) with the required attribution. No LLM in the fact path (cf. `tools/parse_lehrplan.py`).

Run:  python tools/fetch_geo_boundaries.py            # fetch all configured sets
      python tools/fetch_geo_boundaries.py --list     # show config
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import urllib.request
from pathlib import Path

_GEO_DIR = Path(__file__).resolve().parent.parent / "teachersaid" / "grounding" / "geo"

# geo_id -> fetch config. Austria Bundesländer: Statistik Austria OGD boundaries (CC BY 4.0),
# simplified + republished by Flooh Perlot (CC BY 4.0). Names match the Bundesländer dataset.
BOUNDARIES: dict[str, dict] = {
    "at_bundeslaender": {
        "url": "https://raw.githubusercontent.com/ginseng666/GeoJSON-TopoJSON-Austria/"
               "master/2021/simplified-95/laender_95_geo.json",
        "name_field": "name",
        "expected_n": 9,
        "expected_names": ["Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich",
                           "Salzburg", "Steiermark", "Tirol", "Vorarlberg", "Wien"],
        "title": "Österreichische Bundesländer — Verwaltungsgrenzen (2021, vereinfacht)",
        "source": {
            "publisher": "Statistik Austria / Flooh Perlot",
            "title": "Bundesländergrenzen (data.statistik.gv.at, aufbereitet)",
            "url": "https://github.com/ginseng666/GeoJSON-TopoJSON-Austria",
            "licence": "CC BY 4.0",
            "licence_url": "https://creativecommons.org/licenses/by/4.0/",
            "redistributable": True,
            # no role prefix here — the map recipe labels the two fact roles itself
            # ("Daten: … · Grenzen: …"); a prefix in the data doubled to "Grenzen: Grenzen:"
            "attribution": "Statistik Austria – data.statistik.gv.at; "
                           "Aufbereitung: Flooh Perlot (CC BY 4.0)",
            "retrieved": "2026-06-30",
        },
    },
}


def _http_get(url: str) -> bytes:
    ctx = ssl.create_default_context()
    ca = os.environ.get("REQUESTS_CA_BUNDLE") or "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        ctx.load_verify_locations(ca)
    req = urllib.request.Request(url, headers={"User-Agent": "TeachersAid-geo-fetch/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=40) as r:  # noqa: S310 (https only)
        return r.read()


def validate(raw: bytes, cfg: dict) -> dict:
    """Parse + sanity-check a boundary FeatureCollection (pure; unit-tested offline)."""
    fc = json.loads(raw)
    if fc.get("type") != "FeatureCollection":
        raise ValueError("not a GeoJSON FeatureCollection")
    feats = fc.get("features") or []
    nf = cfg["name_field"]
    names = [f.get("properties", {}).get(nf) for f in feats]
    if len(feats) != cfg["expected_n"]:
        raise ValueError(f"expected {cfg['expected_n']} features, got {len(feats)}")
    missing = set(cfg["expected_names"]) - set(names)
    if missing:
        raise ValueError(f"missing expected regions: {sorted(missing)}")
    for f in feats:
        if f.get("geometry", {}).get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("a feature has no (Multi)Polygon geometry")
    return fc


def _update_catalog(geo_id: str, cfg: dict, filename: str, n: int) -> None:
    cat_path = _GEO_DIR / "_catalog.json"
    cat = (json.loads(cat_path.read_text(encoding="utf-8"))
           if cat_path.exists() else {"boundaries": []})
    entry = {"id": geo_id, "title": cfg["title"], "file": filename,
             "name_field": cfg["name_field"], "n_features": n, "source": cfg["source"]}
    cat["boundaries"] = [e for e in cat.get("boundaries", []) if e["id"] != geo_id] + [entry]
    cat["boundaries"].sort(key=lambda e: e["id"])
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch(geo_id: str) -> Path:
    cfg = BOUNDARIES[geo_id]
    if not cfg["source"].get("redistributable"):
        raise ValueError(f"{geo_id}: source not marked redistributable — refusing to store")
    fc = validate(_http_get(cfg["url"]), cfg)
    _GEO_DIR.mkdir(parents=True, exist_ok=True)
    out = _GEO_DIR / f"{geo_id}.geojson"
    out.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    _update_catalog(geo_id, cfg, out.name, len(fc["features"]))
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("ids", nargs="*", help="geo_ids to fetch (default: all)")
    a = ap.parse_args(argv)
    if a.list:
        for gid, cfg in BOUNDARIES.items():
            print(f"{gid}  <-  {cfg['url']}  ({cfg['source']['licence']})")
        return
    for gid in (a.ids or list(BOUNDARIES)):
        p = fetch(gid)
        print(f"stored {gid}: {p}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
