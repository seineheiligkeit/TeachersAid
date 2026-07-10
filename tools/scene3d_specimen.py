"""SPECIMEN — the promoted 3D solid engine (roadmap A7): axonometric_solid + riss_pair.

Renders every school solid (Quader/Würfel · Prisma · Pyramide · Drehzylinder · Drehkegel) in both
recipes at typical GZ values, in a student (measures masked, "h = ?") and a solution (measures
shown) variant, plus a greyscale twin of each to prove the hidden-edge dashing survives a black-and-
white photocopy. Contact sheets group them.

    python -m tools.scene3d_specimen        # -> runs/scene3d_*.png  (+ _bw greyscale + contact sheets)

This is the visual proving-ground the promotion is checked against (mirrors tools/plane3d_specimen.py
for the plane/conic family). All geometry is computed in pipeline/scene3d.py; nothing here is drawn
to look right.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from PIL import Image  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import scene3d as s3  # noqa: E402
from teachersaid.pipeline.scene import scene_to_png  # noqa: E402

# typical GZ classroom values per solid (Kantenlängen/Radien/Höhen in cm)
_SOLIDS = [
    ("wuerfel", dict(a=4, b=4, c=4), {"a": "a = 4 cm", "b": "a = 4 cm", "c": "a = 4 cm"}),
    ("quader", dict(a=5, b=3, c=2.5), {"a": "a = 5", "b": "b = 3", "c": "c = 2,5"}),
    ("prism", dict(n=6, r=2.4, h=4.0), {"r": "r = 2,4", "h": "h = 4"}),
    ("pyramid", dict(n=4, r=2.6, h=4.2), {"r": "a = 2,6", "h": "h = 4,2"}),
    ("cylinder", dict(r=2.0, h=4.0), {"r": "r = 2", "h": "h = 4"}),
    ("cone", dict(r=2.4, h=4.4), {"r": "r = 2,4", "h": "h = 4,4"}),
]


def _greyscale(png: Path) -> Path:
    out = png.with_name(png.stem + "_bw.png")
    Image.open(png).convert("L").save(out)
    return out


def _render(scene, name: str, dpi: int = 160) -> tuple[Path, Path]:
    col = scene_to_png(scene, RUNS_DIR / f"{name}.png", dpi=dpi)
    bw = _greyscale(col)
    print("wrote", col.name, "+", bw.name)
    return col, bw


def _contact_sheet(cols: list[Path], out: Path, per_row: int = 2) -> Path:
    ims = [Image.open(p).convert("RGB") for p in cols]
    w = max(im.width for im in ims)
    h = max(im.height for im in ims)
    rows = (len(ims) + per_row - 1) // per_row
    sheet = Image.new("RGB", (w * per_row, h * rows), "white")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % per_row) * w, (i // per_row) * h))
    sheet.save(out)
    print("wrote", out.name)
    return out


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    axo_solution: list[Path] = []
    axo_student: list[Path] = []
    riss_all: list[Path] = []

    for kind, params, labels in _SOLIDS:
        # axonometric — SOLUTION (measures shown, real values)
        col, _ = _render(s3.axonometric_solid_scene(kind, labels=labels, **params),
                         f"scene3d_axo_{kind}_loesung")
        axo_solution.append(col)
        # axonometric — STUDENT (measures masked: "h = ?")
        col, _ = _render(s3.axonometric_solid_scene(kind, show_measures=False, **params),
                         f"scene3d_axo_{kind}_aufgabe")
        axo_student.append(col)
        # riss pair (zugeordnete Normalrisse)
        col, _ = _render(s3.riss_pair_scene(kind, **params), f"scene3d_riss_{kind}")
        riss_all.append(col)

    _contact_sheet(axo_solution, RUNS_DIR / "scene3d_axo_loesung_kontaktblatt.png")
    _contact_sheet(axo_student, RUNS_DIR / "scene3d_axo_aufgabe_kontaktblatt.png")
    _contact_sheet(riss_all, RUNS_DIR / "scene3d_riss_kontaktblatt.png")
    # a greyscale contact sheet of the solutions — the photocopy test for the hidden-edge dashing
    _contact_sheet([p.with_name(p.stem + "_bw.png") for p in axo_solution],
                   RUNS_DIR / "scene3d_axo_loesung_bw_kontaktblatt.png")


if __name__ == "__main__":
    main()
