"""Code-generated, correct-by-construction assets (schema §6 MediaPolicy).

Content-bearing visuals are built by code (matplotlib), never diffusion. An asset
marked `intentionally_flawed` (v0.4 B3) is built WRONG ON PURPOSE — the builder
must not silently correct it; that is the whole pedagogical point (worked-examples
Ex.2, the geschönte Kurve).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402

from ..config import RUNS_DIR  # noqa: E402
from ..schema.assets import Asset  # noqa: E402


def _outdir() -> Path:
    d = RUNS_DIR / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _em_spectrum(asset: Asset, path: Path) -> None:
    """EM spectrum, ordered by energy. correctness_surface: energy increases
    left→right; ionizing threshold marked. watch-out lives on the InfoBlock, not
    here — the figure itself is correct."""
    bands = [
        ("Radio", 1e-9), ("Mikro", 1e-6), ("IR", 1e-3),
        ("sichtbar", 2.0), ("UV", 1e2), ("Röntgen", 1e4), ("Gamma", 1e6),
    ]
    labels = [b[0] for b in bands]
    energies = [b[1] for b in bands]
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    xs = range(len(bands))
    ax.bar(xs, [1] * len(bands), color="#dce6f2", edgecolor="#33506e")
    for x, lab in zip(xs, labels):
        ax.text(x, 0.5, lab, ha="center", va="center", fontsize=9)
    # ionizing threshold between UV and Röntgen (>~10 eV ionizing)
    thr = 4.5
    ax.axvline(thr, color="#b03a2e", linestyle="--", linewidth=1.5)
    ax.text(thr + 0.05, 1.05, "ionisierend →", color="#b03a2e", fontsize=8, va="bottom")
    ax.text(thr - 0.05, 1.05, "← nicht-ionisierend", color="#2e6b3a", fontsize=8,
            va="bottom", ha="right")
    ax.set_xlim(-0.6, len(bands) - 0.4)
    ax.set_ylim(0, 1.3)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlabel("Energie nimmt zu  →", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _truncated_axis(asset: Asset, path: Path) -> None:
    """A bar chart with a TRUNCATED y-axis — intentionally misleading. Do NOT
    'fix' the axis: the task is to spot the manipulation (geschönte Kurve)."""
    years = ["2019", "2020", "2021", "2022"]
    values = [101.0, 101.4, 101.9, 102.3]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.bar(years, values, color="#c0504d")
    ax.set_ylim(100.5, 102.5)  # <-- the trick: zoomed axis exaggerates change
    ax.set_ylabel("Index")
    ax.set_title("Dramatischer Anstieg?!")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _honest_axis(asset: Asset, path: Path) -> None:
    """The same data with a zero-based axis — the teacher-only honest comparison."""
    years = ["2019", "2020", "2021", "2022"]
    values = [101.0, 101.4, 101.9, 102.3]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.bar(years, values, color="#4f6f52")
    ax.set_ylim(0, 110)  # zero-based: the change is tiny
    ax.set_ylabel("Index")
    ax.set_title("Dieselben Daten, ehrliche Achse")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


_BUILDERS = {
    "matplotlib:em_spectrum": _em_spectrum,
    "matplotlib:truncated_axis": _truncated_axis,
    "matplotlib:honest_axis": _honest_axis,
}


def build_asset(asset: Asset, outdir: Path | None = None) -> Path:
    """Render an asset to a PNG and return its path.

    Guard: an intentionally_flawed asset must route to a builder that preserves
    the flaw; we never substitute a 'corrected' generator.
    """
    outdir = outdir or _outdir()
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{asset.id}.png"
    builder = _BUILDERS.get(asset.generator or "")
    if builder is None:
        raise ValueError(
            f"no code generator for asset '{asset.id}' (generator={asset.generator!r}); "
            "content-bearing assets must be code-generated"
        )
    if asset.intentionally_flawed and asset.generator == "matplotlib:em_spectrum":
        # defensive: the correct generator must never be used for a flawed asset
        raise ValueError(f"asset {asset.id} marked intentionally_flawed but uses a correct generator")
    builder(asset, path)
    return path
