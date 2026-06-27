"""Inline math typesetting — a LaTeX run → a small PNG embedded inline in a Paragraph.

The product output is German maths; fractions/exponents/roots written as plain text read
as "code-symbols" (a documented incumbent failure). A RichText run with `math=True` carries
LaTeX; here we typeset it via matplotlib mathtext (the same engine as the `math_formula`
asset) to a transparent PNG, scaled to ~body height, so `richtext_markup` can drop it inline
via ReportLab `<img>`. Kept out of `reportlab_base` so that module stays reportlab-only;
results are cached by content hash. `configure(dir)` is called once per PDF build.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

_DIR: Path | None = None
_CACHE: dict[str, tuple[str, float, float]] = {}
_TARGET_H_PT = 11.0   # render to roughly body cap-to-descender height
_DPI = 200


def configure(outdir: str | Path) -> None:
    """Point inline-math output at a directory for this build (idempotent)."""
    global _DIR
    _DIR = Path(outdir)
    _DIR.mkdir(parents=True, exist_ok=True)


def render(latex_str: str) -> tuple[str, float, float] | None:
    """Typeset `latex_str` → (png_path, width_pt, height_pt) scaled to body height.
    Returns None if not configured (caller falls back to italic text)."""
    if _DIR is None:
        return None
    key = hashlib.md5(latex_str.encode("utf-8")).hexdigest()[:16]
    if key in _CACHE:
        return _CACHE[key]
    path = _DIR / f"m_{key}.png"
    if not path.exists():
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, f"${latex_str}$", fontsize=12)
        try:
            fig.savefig(path, dpi=_DPI, bbox_inches="tight", pad_inches=0.02, transparent=True)
        finally:
            plt.close(fig)
    w_px, h_px = Image.open(path).size
    h_pt = _TARGET_H_PT
    w_pt = _TARGET_H_PT * (w_px / h_px)
    result = (path.as_posix(), w_pt, h_pt)
    _CACHE[key] = result
    return result
