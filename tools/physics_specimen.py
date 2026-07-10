"""Preview the physics vector scenes + the labelled-diagram recipe — all computed from the spec.

    python -m tools.physics_specimen     # -> runs/physics_specimen.png (+ two labelled diagrams)

The vector/force family (uniform equal-aspect) renders as one montage; the two "Beschrifte die
Teile" projections render standalone at their own figsize (their margin callouts are MEASURED for
that size, so shrinking them into a shared grid cell would crowd the fixed-point-size labels).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from teachersaid.pipeline.labeled_diagram import VULKAN_SPEC, labeled_parts_scene  # noqa: E402
from teachersaid.pipeline.physics_scenes import (force_diagram_scene,  # noqa: E402
                                                 vector_addition_scene)
from teachersaid.pipeline.scene import render_scene, scene_to_png  # noqa: E402


def render(out: Path | None = None) -> list[Path]:
    # the vector/force family — resultants COMPUTED (3-4-5, 5-12-13), maskable, true to scale
    scenes = [
        ("Kräfteaddition — Spitze an Schaft (3-4-5)",
         vector_addition_scene([{"magnitude": 3, "angle_deg": 0, "label": "F_1"},
                                {"magnitude": 4, "angle_deg": 90, "label": "F_2"}])),
        ("Kräfteparallelogramm (Resultierende berechnet)",
         vector_addition_scene([{"magnitude": 5, "angle_deg": 20, "label": "F_1"},
                                {"magnitude": 4, "angle_deg": 80, "label": "F_2"}],
                               method="parallelogram")),
        ("Drei Kräfte aneinandergehängt",
         vector_addition_scene([{"magnitude": 2, "angle_deg": 30, "label": "F_1"},
                                {"magnitude": 3, "angle_deg": 100, "label": "F_2"},
                                {"magnitude": 2.5, "angle_deg": 200, "label": "F_3"}])),
        ("Aufgabe: F_R = ? (Szene maskiert)",
         vector_addition_scene([{"magnitude": 3, "angle_deg": 0, "label": "F_1"},
                                {"magnitude": 4, "angle_deg": 90, "label": "F_2"}],
                               show_value=False)),
        ("Kräfteplan — Gleichgewicht (F_res = 0 N)",
         force_diagram_scene([{"magnitude": 15, "angle_deg": 90, "label": "F_N"},
                              {"magnitude": 15, "angle_deg": 270, "label": "F_G"}],
                             body_label="m", show_resultant=True)),
        ("Kräfteplan — Resultierende (5-12-13)",
         force_diagram_scene([{"magnitude": 12, "angle_deg": 0, "label": "F_Zug"},
                              {"magnitude": 5, "angle_deg": 270, "label": "F_G"}],
                             show_resultant=True)),
    ]
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.2), layout="constrained")
        for ax, (title, sc) in zip(axes.flat, scenes):
            render_scene(sc, ax)
            ax.set_title(title, loc="left", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)
        fig.suptitle("Physik-Szenen — Kräfteaddition (Spitze an Schaft · Parallelogramm) und der "
                     "Kräfteplan. Die Resultierende ist aus der Komponentensumme berechnet, "
                     "maßstabsgetreu und maskierbar (F_R = ?).",
                     fontsize=13.5, fontweight="bold", color=fs.PALETTE.ink)
        out = out or (RUNS_DIR / "physics_specimen.png")
        fig.savefig(out, dpi=150)
        plt.close(fig)

    # the labelled diagram — one spec, two projections (numbered task ↔ named solution)
    named = scene_to_png(labeled_parts_scene(VULKAN_SPEC, show_names=True),
                         RUNS_DIR / "labeled_parts_named.png")
    numbered = scene_to_png(labeled_parts_scene(VULKAN_SPEC, show_names=False),
                            RUNS_DIR / "labeled_parts_numbered.png")
    return [out, named, numbered]


if __name__ == "__main__":
    for p in render():
        print(p)
