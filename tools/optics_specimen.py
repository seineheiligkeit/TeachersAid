"""Preview the optics ray-construction family — every regime + the stage ladder, all COMPUTED
from the thin-lens equation.

    python -m tools.optics_specimen          # -> runs/optics_specimen.png (regimes)
    python -m tools.optics_specimen stages   # -> runs/optics_stages.png   (stage 1–6 ladder)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from teachersaid.pipeline.optics import lens_construction  # noqa: E402
from teachersaid.pipeline.scene import render_scene  # noqa: E402


def render_regimes(out: Path | None = None) -> Path:
    scenes = [
        ("Sammellinse g > 2f — reell, umgekehrt, verkleinert",
         lens_construction("sammellinse", f=3, g=9, G=2, stage=6)),
        ("Sammellinse g = 2f — reell, umgekehrt, gleich groß",
         lens_construction("sammellinse", f=3, g=6, G=2, stage=6)),
        ("Sammellinse f < g < 2f — reell, umgekehrt, vergrößert",
         lens_construction("sammellinse", f=3, g=4.5, G=2, stage=6)),
        ("Sammellinse g < f — virtuell, aufrecht, vergrößert (Lupe)",
         lens_construction("sammellinse", f=3.5, g=2, G=2, stage=6)),
        ("Grenzfall g = f — kein Bild (parallele Strahlen)",
         lens_construction("sammellinse", f=3, g=3, G=2, stage=6)),
        ("Zerstreuungslinse — virtuell, aufrecht, verkleinert",
         lens_construction("zerstreuungslinse", f=3, g=6, G=2, stage=6)),
        ("Aufgabe: B′ = ? (Szene maskiert)",
         lens_construction("sammellinse", f=3, g=4.5, G=2, stage=6, show_value=False)),
        ("Sammellinse — nur Konstruktion (stage 5)",
         lens_construction("sammellinse", f=3, g=9, G=2, stage=5)),
    ]
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(2, 4, figsize=(19.0, 8.8), layout="constrained")
        for ax, (title, sc) in zip(axes.flat, scenes):
            render_scene(sc, ax)
            ax.set_title(title, loc="left", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)
        fig.suptitle("Optik — Bildkonstruktion an dünnen Linsen: die drei Hauptstrahlen. "
                     "Bildlage, Bildgröße und Abbildungsmaßstab aus 1/f = 1/g + 1/b berechnet.",
                     fontsize=13.5, fontweight="bold", color=fs.PALETTE.ink)
        out = out or (RUNS_DIR / "optics_specimen.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        plt.close(fig)
    return out


def render_stages(out: Path | None = None) -> Path:
    scenes = [(f"stage {s}", lens_construction("sammellinse", f=3, g=6, G=2.2, stage=s))
              for s in range(1, 7)]
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.4), layout="constrained")
        for ax, (title, sc) in zip(axes.flat, scenes):
            render_scene(sc, ax)
            ax.set_title(title, loc="left", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)
        fig.suptitle("Bildkonstruktion — der Strahlengang Schritt für Schritt (stage 1–6)",
                     fontsize=13.5, fontweight="bold", color=fs.PALETTE.ink)
        out = out or (RUNS_DIR / "optics_stages.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        plt.close(fig)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stages":
        print(render_stages())
    else:
        print(render_regimes())
        print(render_stages())
