"""Preview the geometric-optics recipes (rectilinear light) — the Lochkamera and the Schattenraum,
both COMPUTED from a small correct-by-construction spec.

    python -m tools.geometric_optics_specimen   # -> runs/geometric_optics_specimen.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from teachersaid.pipeline.geometric_optics import (pinhole_construction,  # noqa: E402
                                                   shadow_construction)
from teachersaid.pipeline.scene import render_scene  # noqa: E402


def render(out: Path | None = None) -> Path:
    scenes = [
        ("Lochkamera — Strahlen kreuzen im Loch → Bild kopfstehend",
         pinhole_construction(G=3, a=6, b=4)),
        ("Lochkamera — größere Bildweite (b > a → vergrößert)",
         pinhole_construction(G=2.5, a=4, b=7)),
        ("Lochkamera — Aufgabe: Bildgröße B = ? (Angaben sichtbar)",
         pinhole_construction(G=3, a=6, b=4, show_value=False)),
        ("Schattenraum — Punktquelle → scharfer Kernschatten (mit Wand)",
         shadow_construction(source=(-6.5, 0.0), center=(0.0, 0.0), r=1.5, screen_x=6.5)),
        ("Schattenraum — nähere Quelle → stärker divergierender Schattenkegel",
         shadow_construction(source=(-4.5, 0.0), center=(0.0, 0.0), r=1.5, screen_x=6.0)),
        ("Schattenraum — ohne Wand (nur der Schattenraum)",
         shadow_construction(source=(-6.5, 0.0), center=(0.0, 0.0), r=1.4, screen_x=None)),
    ]
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(2, 3, figsize=(19.0, 8.8), layout="constrained")
        for ax, (title, sc) in zip(axes.flat, scenes):
            render_scene(sc, ax)
            ax.set_title(title, loc="left", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)
        fig.suptitle("Geometrische Optik — geradlinige Lichtausbreitung: Lochkamera (Kreuzung "
                     "im Loch) und Schattenraum (Tangentenkonstruktion), beide berechnet.",
                     fontsize=13.5, fontweight="bold", color=fs.PALETTE.ink)
        out = out or (RUNS_DIR / "geometric_optics_specimen.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        plt.close(fig)
    return out


if __name__ == "__main__":
    print(render())
