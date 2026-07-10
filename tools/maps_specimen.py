"""Specimen sheet for the CHOROPLETH map recipe after the figstyle port (A1).

The thematic map — sourced boundaries (facts) filled from a cited dataset. Now on the semantic
roles: region borders = paper, labels/leaders = ink/muted, an unmapped region = no_data, the
Wien-in-Niederösterreich enclave leadered out below. LOOK at label placement + the colourbar.

    python -m tools.maps_specimen [OUTDIR]     # default: runs/specimens/maps
"""
from __future__ import annotations

import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline.assets import build_asset
from teachersaid.schema.assets import Asset


def render(outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    from teachersaid.grounding import data_store as ds
    dset = ds.get_dataset("statistik_austria_bundeslaender_2024")
    series = dset.series["bevoelkerung"]
    values = dict(zip(series["groups"], series["counts"]))
    a = Asset(id="choropleth_bundeslaender", role="figure", generator="matplotlib:choropleth_map",
              spec={"geo_id": "at_bundeslaender", "values": values,
                    "value_label": "Einwohner:innen", "title": "Bevölkerung nach Bundesland"})
    return [build_asset(a, outdir=outdir)]


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS_DIR / "specimens" / "maps"
    for p in render(out):
        print(p)
