"""Reads the curated grounded-facts datasets at `grounding/data/`.

The data-layer twin of `lehrplan_store.py`: it reads the deterministic fetch-tool
output (`grounding/data/_catalog.json` + per-dataset `<id>.json`, written by
`tools/fetch_statistik_austria.py` and gated by HITL review) and adapts it to the
engine schema (`Dataset` / `SourceRef` / `DataRef`). It is the *resolver* for the
data layer — the analogue of `pipeline/resolve.py` for competences: it never
authors a number or a citation, it only looks one up and fills the cited reference.
"""

from __future__ import annotations

import json
from functools import lru_cache

from ..config import GROUNDING_DATA
from ..schema.datasets import DataRef, Dataset, SourceRef


@lru_cache(maxsize=1)
def _catalog() -> dict:
    p = GROUNDING_DATA / "_catalog.json"
    if not p.exists():
        return {"datasets": []}
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _dataset_raw(dataset_id: str) -> dict | None:
    entry = next((d for d in _catalog().get("datasets", []) if d.get("id") == dataset_id), None)
    fname = (entry or {}).get("file") or f"{dataset_id}.json"
    p = GROUNDING_DATA / fname
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def get_dataset(dataset_id: str) -> Dataset | None:
    raw = _dataset_raw(dataset_id)
    return Dataset.model_validate(raw) if raw else None


def list_datasets() -> list[Dataset]:
    out = [get_dataset(d["id"]) for d in _catalog().get("datasets", [])]
    return [d for d in out if d is not None]


def source_ref_for(dataset_id: str) -> SourceRef | None:
    ds = get_dataset(dataset_id)
    return ds.source if ds else None


def series_for(dataset_id: str, series: str | None) -> dict | None:
    ds = get_dataset(dataset_id)
    if ds is None or series is None:
        return None
    return ds.series.get(series)


import re

_TERM = re.compile(r"[a-zäöüß0-9]+")


def _terms(text: str) -> set[str]:
    return {t for t in _TERM.findall((text or "").casefold()) if len(t) > 3}


def relevant_datasets(
    *, subject: str | None = None, topic: str | None = None,
    competences: list[str] | None = None,
) -> list[Dataset]:
    """Find datasets a worksheet could build tasks AROUND — the data ⇄ ideas interplay.
    Deterministic (no LLM, mirrors compose's angle-scoring): subject-code match, topic↔
    keyword/title term overlap, competence-id overlap. With no filter → all datasets;
    with filters → those scoring > 0, best first."""
    comps = set(competences or [])
    topic_terms = _terms(topic or "")
    scored: list[tuple[float, Dataset]] = []
    for d in list_datasets():
        if subject is None and not topic_terms and not comps:
            scored.append((0.0, d))
            continue
        score = 0.0
        if subject and subject in d.subjects:
            score += 2.0
        if topic_terms:
            kw = {w for k in d.keywords for w in _terms(k)} | _terms(d.title)
            score += len(topic_terms & kw)
        if comps:
            score += 3.0 * len(comps & set(d.competences))
        if score > 0:
            scored.append((score, d))
    scored.sort(key=lambda s: (-s[0], s[1].id))
    return [d for _, d in scored]


def _series_spec(series: dict, generator: str) -> dict:
    """Map a dataset series → the value fields the recipe needs (real numbers replace
    any LLM-authored ones; presentation fields like title/labels are left untouched)."""
    g = (generator or "").split(":")[-1]
    if g == "population_pyramid":
        return {k: series[k] for k in ("age_groups", "male", "female") if k in series}
    if g == "bar_chart":
        cats = series.get("groups") or series.get("categories") or series.get("age_groups")
        vals = series.get("values") or series.get("shares_pct") or series.get("counts")
        return {k: v for k, v in {"categories": cats, "values": vals}.items() if v is not None}
    if g == "line":
        cats = series.get("categories") or series.get("x") or series.get("years")
        vals = series.get("values") or series.get("y")
        return {k: v for k, v in {"categories": cats, "values": vals}.items() if v is not None}
    if g == "climate_diagram":
        return {k: series[k] for k in ("months", "temp", "precip") if k in series}
    if g == "timeline":
        if series.get("events"):
            return {"events": series["events"]}
        cats = series.get("categories") or series.get("labels")
        vals = series.get("values") or series.get("years")
        return {k: v for k, v in {"categories": cats, "values": vals}.items() if v is not None}
    if g == "choropleth_map":                 # a thematic map: {region_name: value}
        groups = series.get("groups") or series.get("categories")
        vals = series.get("counts") or series.get("values") or series.get("shares_pct")
        if groups and vals:
            return {"values": {str(k): v for k, v in zip(groups, vals)}}
        return {}
    return {}


def series_to_spec(ref: DataRef, generator: str) -> tuple[dict, list[str]]:
    """The single resolve+map function (used by data_ground to FILL values and by
    figure_lint to WARN). Returns (spec_fields, notes); honest gaps are notes, not crashes."""
    ds = get_dataset(ref.dataset_id)
    if ds is None:
        return {}, [f"Datensatz '{ref.dataset_id}' nicht im grounding/data-Katalog"]
    if ref.series is None:
        return {}, []                                   # citation-only reference, no figure values
    series = ds.series.get(ref.series)
    if series is None:
        return {}, [f"Datensatz '{ref.dataset_id}' hat keine Serie '{ref.series}'"]
    spec = _series_spec(series, generator)
    if not spec:
        return {}, [f"Serie '{ref.series}' liefert keine Werte für Generator '{generator}'"]
    return spec, []


def format_available_datasets(datasets: list[Dataset]) -> str:
    """A German brief block listing citable datasets for a generation prompt — so the
    model builds tasks around real data and sets `data_source` instead of inventing numbers."""
    if not datasets:
        return ""
    lines = [
        "## Verfügbare echte Datensätze (für `data_source` — echte, zitierte Zahlen)",
        "Zeigt eine Abbildung echte Zahlen, **erfinde sie nicht**: setze auf der Figur "
        '`"data_source": {"dataset_id":"<id>","series":"<serie>"}`. Das System übernimmt dann '
        "die echten Werte aus dem Datensatz und zeigt die Quelle an. Wähle Kernfragen/Aufgaben "
        "ruhig danach, welche dieser Daten gut passen:",
    ]
    for d in datasets:
        series = " · ".join(
            f"`{k}` ({v.get('label', k)})" for k, v in d.series.items())
        lines.append(f"- `{d.id}` — {d.title}. Serien: {series}. {d.source.attribution}")
    return "\n".join(lines)


def resolve_dataref(ref: DataRef) -> tuple[DataRef, list[str]]:
    """Fill a DataRef's cited fields (attribution/stand/title/url) from the dataset's
    SourceRef — *select, never author*: the citation is taken from the vetted dataset,
    never trusted from whatever was hand-written on the ref. Returns (resolved, notes);
    an unknown dataset/series is an honest gap note (surfaced by verify), not a crash."""
    notes: list[str] = []
    ds = get_dataset(ref.dataset_id)
    if ds is None:
        notes.append(f"Datensatz '{ref.dataset_id}' nicht im grounding/data-Katalog")
        return ref, notes
    src = ds.source
    if ref.series and ref.series not in ds.series:
        notes.append(f"Datensatz '{ref.dataset_id}' hat keine Serie '{ref.series}'")
    resolved = ref.model_copy(update={
        "title": ds.title,
        "url": src.url,
        "attribution": src.attribution,
        "stand": src.stand,
    })
    return resolved, notes
