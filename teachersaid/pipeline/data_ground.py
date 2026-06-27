"""Ground figure data (deterministic) — for every asset with a `data_source`, FILL its
values from the vetted dataset slice AND stamp the resolved citation onto it.

This is "select, never author" made real for numbers: the figure's values come FROM the
dataset (overwriting anything the model authored), and the citation text comes FROM the
dataset's SourceRef (not from whatever was hand-written). Runs inside `assemble`, so by
render time every sourced figure carries real numbers + its citation ON the content
object — which keeps `rendering/` pure (schema-only). Honest gaps (unknown dataset/series,
no value mapping for the generator) come back as notes for verify to surface.
"""

from __future__ import annotations

from ..grounding.data_store import resolve_dataref, series_to_spec
from ..schema.worksheet import WorksheetContent


def ground_data(content: WorksheetContent) -> list[str]:
    """Resolve+stamp citations and fill real values on every asset with a data_source.
    Returns gap notes; mutates assets in place. Presentation fields (title/labels) are
    preserved — only the value/category fields are replaced with the real ones."""
    notes: list[str] = []
    for a in content.assets:
        if a.data_source is None:
            continue
        resolved, cite_notes = resolve_dataref(a.data_source)
        a.data_source = resolved
        spec_fields, map_notes = series_to_spec(a.data_source, a.generator or "")
        if spec_fields:
            a.spec = {**(a.spec or {}), **spec_fields}   # real numbers replace authored ones
        notes += [f"{a.id}: {n}" for n in cite_notes + map_notes]
    return notes
