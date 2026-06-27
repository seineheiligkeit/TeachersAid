"""JSON-file-backed store for the grounded-facts dataset library (HITL review).

Parallel to `AssetStore`/`BlockStore`: each curated dataset (fetched + parsed by a
deterministic tool into `grounding/data/`, see `tools/fetch_statistik_austria.py`)
is staged here as a reviewable `DatasetRecord` so a human vets the source, licence,
and figures before content may cite it — exactly the gate the Lehrplan catalog gets.
`upsert` preserves review status (re-seeding never un-approves). The *durable*
artifact is the dataset JSON under `grounding/data/`; this store holds the review
state + a copy for the dashboard.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..schema.datasets import Dataset
from .base import JsonStore


class DatasetRecord(BaseModel):
    """A curated dataset plus library metadata for review (mirrors LibraryAsset)."""
    model_config = ConfigDict(extra="forbid")
    id: str
    dataset: Dataset
    status: str = "in_review"           # in_review | approved | rejected
    source: str = "curated"            # curated (tool-fetched) | user
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        d = self.dataset
        return {
            "id": self.id, "title": d.title,
            "publisher": d.source.publisher, "licence": d.source.licence,
            "redistributable": d.source.redistributable, "stand": d.source.stand,
            "retrieved": d.source.retrieved, "url": d.source.url,
            "attribution": d.source.attribution,
            "series": list(d.series.keys()), "unit": d.unit, "totals": d.totals,
            "status": self.status, "source": self.source, "updated_at": self.updated_at,
        }


class DatasetStore(JsonStore[DatasetRecord]):
    model = DatasetRecord
    subdir = "datasets"

    def list(self, *, status: str | None = None) -> list[DatasetRecord]:
        return self._list(where=lambda r: status is None or r.status == status,
                          sort_key=lambda r: r.id)

    def approved(self) -> list[DatasetRecord]:
        return self.list(status="approved")
