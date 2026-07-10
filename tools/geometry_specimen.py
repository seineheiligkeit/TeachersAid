"""Specimen sheet for the GEOMETRY / coordinate recipe family after the figstyle port (A1).

right_triangle · rectangle · polygon are now computed `Scene`s (rendered by `render_scene`);
circle · coordinate_plane · function_graph · tree_diagram stay matplotlib-on-figstyle. All draw
through the semantic roles (surface fill, ink edge, the unknown in `focus`). Rendered with
realistic classroom specs; LOOK at them and tune.

    python -m tools.geometry_specimen [OUTDIR]     # default: runs/specimens/geometry
"""
from __future__ import annotations

import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline.assets import build_asset
from teachersaid.schema.assets import Asset

CASES: dict[str, dict] = {
    "right_triangle": {"a": 4, "b": 3, "label_a": "a = 4 cm", "label_b": "b = 3 cm",
                       "label_c": "c = ?", "title": "Satz des Pythagoras"},
    "rectangle": {"length": 6, "width": 3.5, "label_l": "l = 6 cm", "label_w": "b = 3,5 cm",
                  "title": "Flächeninhalt eines Rechtecks"},
    "polygon": {"points": [[0, 0], [5, 0], [6, 3], [2.5, 4.5], [-1, 2.5]],
                "vertex_labels": ["A", "B", "C", "D", "E"],
                "side_labels": ["a", "b", "c", "d", "e"], "title": "Fünfeck ABCDE"},
    "polygon_triangle": {"points": [[0, 0], [6, 0], [1.8, 4.2]],
                         "vertex_labels": ["A", "B", "C"], "side_labels": ["c", "a", "b"],
                         "title": "Dreieck — Seiten und Ecken"},
    "circle": {"radius": 3, "label_r": "r = 3 cm", "title": "Kreis — Umfang und Fläche"},
    "coordinate_plane": {"points": [{"x": 1, "y": 2, "label": "A"}, {"x": 5, "y": 4, "label": "B"},
                                    {"x": 4, "y": -1, "label": "C"}], "segments": [[0, 1], [1, 2]],
                         "xmin": -2, "xmax": 6, "ymin": -2, "ymax": 5, "title": "Strecke im Gitter"},
    "function_graph": {"xmin": -1, "xmax": 6, "m": 0.5, "b": 1, "xlabel": "t (s)",
                       "ylabel": "v (m/s)", "title": "Gleichförmige Beschleunigung"},
    "function_graph_pts": {"xmin": 0, "xmax": 6, "points": [[0, 0], [1, 2], [2, 4], [3, 6], [4, 6],
                           [5, 6]], "connect": True, "xlabel": "t (s)", "ylabel": "v (m/s)",
                           "title": "v-t-Diagramm"},
    "tree_diagram": {"title": "Zweistufiger Zufallsversuch", "branches": [
        {"label": "rot", "p": "0,4", "children": [{"label": "rot", "p": "0,3"},
                                                  {"label": "blau", "p": "0,7"}]},
        {"label": "blau", "p": "0,6", "children": [{"label": "rot", "p": "0,5"},
                                                   {"label": "blau", "p": "0,5"}]}]},
}

_GEN = {"polygon_triangle": "matplotlib:polygon", "function_graph_pts": "matplotlib:function_graph"}


def render(outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, spec in CASES.items():
        gen = _GEN.get(name, "matplotlib:" + name)
        paths.append(build_asset(Asset(id=name, role="figure", generator=gen, spec=spec),
                                 outdir=outdir))
    return paths


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS_DIR / "specimens" / "geometry"
    for p in render(out):
        print(p)
