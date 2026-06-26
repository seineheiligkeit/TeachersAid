"""The decorative kit — content-free, reusable assets (Phase 4 #4).

A small curated starter set built by the `svg:` backend (crisp, no extra dep —
rasterised via PyMuPDF). Decorative means **content-free**: these carry no answer
and no claim, so the media-policy gate admits them from any source. They seed into
the `AssetStore` for SME review, then become reusable framing for composed sheets.

Add more here, or via the dashboard; a diffusion-produced decorative asset (once
the SME's `diffusion:` backend is wired) joins the same store the same way.
"""

from __future__ import annotations

from ..schema.assets import Asset

# id, generator, spec, tags, caption
_KIT: list[tuple[str, str, dict, list[str], str]] = [
    ("kit-banner-warm", "svg:banner", {"color": "#b5651d"}, ["banner", "header"],
     "Dekorative Kopfleiste (warm)."),
    ("kit-banner-cool", "svg:banner", {"color": "#33506e"}, ["banner", "header"],
     "Dekorative Kopfleiste (kühl)."),
    ("kit-motif-green", "svg:motif", {"color": "#2e6b3a"}, ["motif", "corner"],
     "Eck-Motiv (grün)."),
    ("kit-motif-blue", "svg:motif", {"color": "#4f6f8f"}, ["motif", "corner"],
     "Eck-Motiv (blau)."),
    ("kit-badge-phy", "svg:badge", {"label": "PHY", "color": "#b5651d"},
     ["badge", "Physik"], "Fach-Badge Physik."),
    ("kit-badge-mat", "svg:badge", {"label": "MAT", "color": "#33506e"},
     ["badge", "Mathematik"], "Fach-Badge Mathematik."),
    ("kit-badge-deu", "svg:badge", {"label": "DEU", "color": "#2e6b3a"},
     ["badge", "Deutsch"], "Fach-Badge Deutsch."),
    ("kit-badge-gwb", "svg:badge", {"label": "GWB", "color": "#8a5a2b"},
     ["badge", "Geographie und wirtschaftliche Bildung"], "Fach-Badge GWB."),
]


def kit_assets() -> list[tuple[Asset, list[str]]]:
    """The kit as (Asset, tags) pairs — role 'decoration' so the gate treats them
    as decorative (content-free), buildable via the svg: backend."""
    return [
        (Asset(id=aid, role="decoration", generator=gen, spec=spec, caption=cap), tags)
        for aid, gen, spec, tags, cap in _KIT
    ]


def seed_assets(store=None, *, status: str = "in_review") -> list:
    """Seed the decorative kit into the asset library for review. Idempotent:
    `upsert` preserves the status of an asset already reviewed."""
    from ..pipeline import orchestrator as orch
    from ..store.assetstore import AssetStore

    store = store or AssetStore()
    out = []
    for asset, tags in kit_assets():
        out.append(orch.ingest_asset(
            store, asset, klass="decorative", tags=tags, source="curated", status=status))
    return out
