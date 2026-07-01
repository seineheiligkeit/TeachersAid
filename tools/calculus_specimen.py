"""Preview the analysis scene family — the full wishlist, all computed from the term.

    python -m tools.calculus_specimen     # -> runs/calculus_specimen.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from teachersaid.pipeline.calculus import (area_between_scene, distribution_scene,  # noqa: E402
                                           extrema_scene, function_scene, integral_scene,
                                           riemann_scene, tangent_scene)
from teachersaid.pipeline.scene import render_scene  # noqa: E402


def render(out: Path | None = None) -> Path:
    scenes = [
        ("Funktionsgraph (beliebiger Term)", function_scene("sin(x)", -6.6, 6.6, label="f")),
        ("Integral — Fläche (Wert berechnet)", integral_scene("0.2*x**2+1", 1, 4, label="f")),
        ("Riemann-Summe — Näherung an ∫", riemann_scene("0.2*x**2+1", 1, 4, n=6, mode="left", label="f")),
        ("Tangente — Ableitung als Steigung", tangent_scene("0.25*x**2", 2, xmin=-1, xmax=5, label="f")),
        ("Extrema — Hoch-/Tiefpunkt (f'=0)", extrema_scene("x**3-3*x", -3, 3, label="f")),
        ("Fläche zwischen zwei Kurven", area_between_scene("x**2", "0.5*x+1.5", label="f")),
        ("Normalverteilung — P(X ≥ 1)", distribution_scene(0, 1, a=1, mode="ge")),
        ("Aufgabe: A = ? (Szene maskiert)", integral_scene("0.2*x**2+1", 1, 4, show_value=False, label="f")),
    ]
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(2, 4, figsize=(17.5, 8.6), layout="constrained")
        for ax, (title, sc) in zip(axes.flat, scenes):
            render_scene(sc, ax)
            ax.set_title(title, loc="left", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)
        fig.suptitle("Analysis-Szenen — die Kurve, die Fläche (∫), die Steigung, Extrema, "
                     "Fläche zwischen Kurven, Verteilung. Alles aus dem Term berechnet.",
                     fontsize=13.5, fontweight="bold", color=fs.PALETTE.ink)
        out = out or (RUNS_DIR / "calculus_specimen.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        plt.close(fig)
    return out


if __name__ == "__main__":
    print(render())
