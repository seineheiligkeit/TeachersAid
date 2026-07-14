"""Preview the Homologie-Schema recipe — the vertebrate-Bauplan comparison, computed from the
curated limb homologies.

    python -m tools.homology_specimen     # -> runs/homology_specimen.png

The forelimb pair (focus) and the hindlimb pair (primary) carry the SAME two colours on every
animal, while the SHAPE varies (Flossen · Beine · Flügel) — homolog, verschieden geformt. The
figure is the honest replacement for a "count the limb pairs" bar chart: it invites "same two
pairs, different form", not "find the differences".
"""
from __future__ import annotations

from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline.homology import homology_scene
from teachersaid.pipeline.scene import scene_to_png


def render(out: Path | None = None) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = out or (RUNS_DIR / "homology_specimen.png")
    return scene_to_png(homology_scene(), out, dpi=150)


if __name__ == "__main__":
    print(render())
