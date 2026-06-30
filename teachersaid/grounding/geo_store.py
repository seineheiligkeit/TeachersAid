"""Load curated geographic boundary sets — the map-figure fact layer.

The spatial twin of `grounding/data_store`: boundaries are FACTS, fetched by
`tools/fetch_geo_boundaries.py` and stored under `grounding/geo/`. The choropleth recipe reads
polygons by a stable `geo_id`; the source citation rides on the figure. *Select, never author.*
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_GEO_DIR = Path(__file__).resolve().parent / "geo"


@lru_cache(maxsize=1)
def _catalog() -> dict:
    p = _GEO_DIR / "_catalog.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"boundaries": []}


def get_entry(geo_id: str) -> dict | None:
    return next((e for e in _catalog().get("boundaries", []) if e["id"] == geo_id), None)


def list_boundaries() -> list[str]:
    return [e["id"] for e in _catalog().get("boundaries", [])]


@lru_cache(maxsize=8)
def load_boundaries(geo_id: str) -> dict:
    """{region_name: GeoJSON geometry} for a boundary set, keyed by its `name_field`."""
    e = get_entry(geo_id)
    if e is None:
        raise KeyError(f"no boundary set '{geo_id}' — run tools/fetch_geo_boundaries.py")
    fc = json.loads((_GEO_DIR / e["file"]).read_text(encoding="utf-8"))
    nf = e["name_field"]
    return {f["properties"][nf]: f["geometry"] for f in fc["features"]}


def get_source(geo_id: str) -> dict | None:
    e = get_entry(geo_id)
    return e["source"] if e else None


def citation(geo_id: str) -> str:
    """The 'Quelle: …' line a map figure prints (Quellenkritik = curriculum)."""
    s = get_source(geo_id) or {}
    return s.get("attribution") or s.get("title") or geo_id
