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
    "at_bezirke_2025": {
        "url": "https://www.statistik.gv.at/gs-open/GEODATA/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=GEODATA:STATISTIK_AUSTRIA_POLBEZ_20250101&outputFormat=application/json&srsName=EPSG:4326",
        "name_field": "g_name",
        "expected_n": 117,
        "expected_names": ["Eisenstadt(Stadt)", "Wien 23.,Liesing"],
        # The WFS also carries the whole-city Wien polygon (g_id 900) on top of
        # its 23 Gemeindebezirke. Population facts use 901–923, so storing 900
        # as well would double-cover Vienna and make the data join ambiguous.
        "exclude_field": "g_id",
        "exclude_values": ["900"],
        "simplify_tolerance": 0.002,
        "title": "Österreichische politische Bezirke – Verwaltungsgrenzen (1.1.2025, vereinfacht)",
        "source": {
            "publisher": "Statistik Austria",
            "title": "Gliederung Österreichs in Politische Bezirke (1.1.2025)",
            "url": "https://data.statistik.gv.at/web/meta.jsp?dataset=OGDEXT_POLBEZ_1",
            "licence": "CC BY 4.0",
            "licence_url": "https://creativecommons.org/licenses/by/4.0/",
            "redistributable": True,
            "attribution": "Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)",
            "retrieved": "2026-07-11",
            "stand": "2025-01-01",
        },
    },
}


def _point_segment_distance(point: list[float], start: list[float], end: list[float]) -> float:
    """Euclidean point-to-segment distance in source coordinate units."""
    px, py = point[:2]
    x1, y1 = start[:2]
    x2, y2 = end[:2]
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    qx, qy = x1 + t * dx, y1 + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _simplify_line(points: list[list[float]], tolerance: float) -> list[list[float]]:
    """Deterministic Ramer–Douglas–Peucker simplification for an open line."""
    if len(points) <= 2:
        return points
    greatest, index = 0.0, 0
    for i in range(1, len(points) - 1):
        distance = _point_segment_distance(points[i], points[0], points[-1])
        if distance > greatest:
            greatest, index = distance, i
    if greatest <= tolerance:
        return [points[0], points[-1]]
    left = _simplify_line(points[:index + 1], tolerance)
    right = _simplify_line(points[index:], tolerance)
    return left[:-1] + right


def _simplify_ring(ring: list[list[float]], tolerance: float) -> list[list[float]]:
    if len(ring) < 5:
        return ring
    core = ring[:-1] if ring[0][:2] == ring[-1][:2] else ring[:]
    pivot = min(range(len(core)), key=lambda i: (core[i][0], core[i][1]))
    rotated = core[pivot:] + core[:pivot]
    far = max(range(1, len(rotated)),
              key=lambda i: ((rotated[i][0] - rotated[0][0]) ** 2
                             + (rotated[i][1] - rotated[0][1]) ** 2))
    first = _simplify_line(rotated[:far + 1], tolerance)
    second = _simplify_line(rotated[far:] + [rotated[0]], tolerance)
    simplified = first[:-1] + second
    if len(simplified) < 4:
        return ring
    if simplified[0][:2] != simplified[-1][:2]:
        simplified.append(simplified[0])
    return simplified


def simplify(fc: dict, tolerance: float) -> dict:
    """Simplify every Polygon/MultiPolygon ring without changing properties."""
    for feature in fc.get("features", []):
        geometry = feature["geometry"]
        polygons = (geometry["coordinates"] if geometry["type"] == "MultiPolygon"
                    else [geometry["coordinates"]])
        simplified = [[_simplify_ring(ring, tolerance) for ring in polygon]
                      for polygon in polygons]
        geometry["coordinates"] = (simplified if geometry["type"] == "MultiPolygon"
                                   else simplified[0])
    return fc


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
    if cfg.get("exclude_field"):
        field = cfg["exclude_field"]
        excluded = {str(value) for value in cfg.get("exclude_values", [])}
        fc["features"] = [feature for feature in fc["features"]
                          if str(feature.get("properties", {}).get(field)) not in excluded]
    if cfg.get("simplify_tolerance"):
        fc = simplify(fc, float(cfg["simplify_tolerance"]))
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
