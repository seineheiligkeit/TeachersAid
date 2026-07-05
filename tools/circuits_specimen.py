"""Preview the circuit-schematic family — series, parallel and mixed (nested) netlists, all
values COMPUTED via Kirchhoff (sympy, exact).

    python -m tools.circuits_specimen       # -> runs/circuits_specimen.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from teachersaid.pipeline.circuits import circuit_construction  # noqa: E402
from teachersaid.pipeline.scene import render_scene  # noqa: E402


def _R(ohm, label):
    return {"type": "resistor", "ohm": ohm, "label": label}


def _L(label):
    return {"type": "lamp", "ohm": 40, "label": label}


SERIES = {"type": "series", "children": [_R(100, "R₁"), _R(220, "R₂"), _R(330, "R₃")]}
PARALLEL = {"type": "parallel", "children": [_R(200, "R₁"), _R(300, "R₂"), _R(600, "R₃")]}
MIXED = {"type": "series", "children": [
    _R(100, "R₁"),
    {"type": "parallel", "children": [_R(200, "R₂"), _R(200, "R₃")]}]}
NESTED = {"type": "parallel", "children": [
    {"type": "series", "children": [_R(100, "R₁"), _R(100, "R₂")]},
    _R(150, "R₃")]}
LAMP = {"type": "series", "children": [_L("L₁"), _R(20, "R₁")]}


def render(out: Path | None = None) -> Path:
    scenes = [
        ("Reihenschaltung — R₁+R₂+R₃", circuit_construction(SERIES, 12)),
        ("Parallelschaltung — 1/R = Σ1/Rᵢ", circuit_construction(PARALLEL, 12)),
        ("Gemischt — R₁ in Reihe zu (R₂∥R₃)", circuit_construction(MIXED, 12)),
        ("Verschachtelt — (R₁+R₂) ∥ R₃", circuit_construction(NESTED, 9)),
        ("Lämpchen (Kreis mit Kreuz) + Widerstand", circuit_construction(LAMP, 6)),
        ("Aufgabe: R₂ = ? — gegeben U, I, R₁, R₃ (mask=[R₂, Rers])",
         circuit_construction(MIXED, 12, ask="R₂", mask=["R₂", "Rers"])),
    ]
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.4), layout="constrained")
        for ax, (title, sc) in zip(axes.flat, scenes):
            render_scene(sc, ax)
            ax.set_title(title, loc="left", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)
        fig.suptitle("Stromkreise — Schaltbilder aus einer Netzliste. Ersatzwiderstand, Ströme "
                     "und Spannungen nach Kirchhoff berechnet (exakt).",
                     fontsize=13.5, fontweight="bold", color=fs.PALETTE.ink)
        out = out or (RUNS_DIR / "circuits_specimen.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        plt.close(fig)
    return out


if __name__ == "__main__":
    print(render())
