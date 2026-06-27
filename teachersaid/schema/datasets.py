"""Grounded-facts data layer (the SME-championed "big bet") — typed citations.

Generalises the grounding discipline from *competences* to *facts*: content states
real numbers that point at a curated, cited, provenance-stamped dataset, instead of
LLM-invented ("schematisch") figures. The load-bearing rule — **select, never
author** — is structural: facts live in a deterministic, vetted dataset (fetched +
parsed by tooling, see `tools/fetch_statistik_austria.py`), and content *references*
a dataset by stable id, exactly as a task's `serves` references a competence.

Three models, mirroring the established patterns:
* `SourceRef` — the publisher/title/url/licence/attribution citation stamp
  (the data analogue of `FassungRef`); `attribution` is the exact string the licence
  requires, rendered verbatim under the figure.
* `DataRef` — a figure/task pointing at {dataset_id, series} (the analogue of `Serves`);
  the resolved citation fields are cached on it so the renderer stays pure.
* `Dataset` — the curated in-repo record under `grounding/data/` (the analogue of a
  `lehrplan/<CODE>.json` entry).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SourceRef(BaseModel):
    """A citation stamp for an openly-licensed public dataset (cf. `FassungRef`)."""
    model_config = ConfigDict(extra="forbid")
    publisher: str
    title: str
    url: str | None = None
    dataset_code: str | None = None          # the publisher's stable dataset id (a DataRef anchor)
    licence: str | None = None
    licence_url: str | None = None
    redistributable: bool = False            # may we embed the values, or reference-only?
    attribution: str                         # the exact citation string the licence requires
    retrieved: str | None = None             # ISO date the tool fetched it
    stand: str | None = None                 # the data's own "Stand" date


class DataRef(BaseModel):
    """A figure/task using real data points at a dataset by stable id + the slice used
    (the factual analogue of `Serves`). `attribution`/`stand`/`title`/`url` are RESOLVED
    from the dataset by `grounding/data_store` (cached so rendering stays schema-pure);
    never hand-authored as the source of truth."""
    model_config = ConfigDict(extra="forbid")
    dataset_id: str
    series: str | None = None                # which series within the dataset
    note: str | None = None                  # human-readable slice description
    # --- resolved/cached from the dataset's SourceRef (filled by data_store) ---
    title: str | None = None
    url: str | None = None
    attribution: str | None = None
    stand: str | None = None

    def citation(self) -> str:
        """The line the projection prints under a figure (Quellenkritik = curriculum)."""
        bits = [self.attribution or self.title or self.dataset_id]
        if self.stand:
            bits.append(f"Stand {self.stand}")
        return " · ".join(b for b in bits if b)


class Dataset(BaseModel):
    """A curated, provenance-stamped dataset — the in-repo record (grounding/data/<id>.json),
    written by a deterministic fetch+parse tool and gated by HITL review. `series` shapes
    vary by dataset (a pyramid carries male/female; a broad-group series carries counts),
    so it stays an open dict; the recipe/figure reads the slice it needs."""
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    source: SourceRef
    unit: str | None = None
    totals: dict = Field(default_factory=dict)
    series: dict = Field(default_factory=dict)   # series_key -> {label, ...values}
    # --- discovery metadata (curated tags, NOT facts) so data ⇄ ideas can interplay:
    # ideation queries the catalog by subject/topic/competence to find data tasks can be
    # built around. HITL-reviewed like the subject_models overlay; never authors a number.
    subjects: list[str] = Field(default_factory=list)      # catalog codes served (GWB, MAT, …)
    keywords: list[str] = Field(default_factory=list)      # German topic-match terms
    competences: list[str] = Field(default_factory=list)   # especially-relevant competence ids
