"""JSON-file-backed store for the Sachverhalt content-layer library (HITL review).

Parallel to `TextStore`/`DatasetStore`: each curated `Sachverhalt` is staged as a reviewable
`SachverhaltRecord` so a human vets the **facts + sources** (the fact-check surface) before a
worksheet derives from it. `upsert` preserves review status (re-seeding never un-approves).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..schema.richtext import plain_text
from ..schema.sachverhalt import Sachverhalt
from .base import JsonStore


class SachverhaltRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    sachverhalt: Sachverhalt
    status: str = "in_review"           # in_review | approved | rejected
    source: str = "curated"
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        s = self.sachverhalt
        return {
            "id": self.id, "title": s.topic, "subject": s.subject,
            "klasse": s.default_klasse(), "klasse_range": list(s.klasse_range),
            "leitfrage": plain_text(s.leitfrage) if s.leitfrage else "",
            "sensitive": s.sensitive,
            "n_timeline": len(s.timeline), "n_actors": len(s.actors),
            "n_causes": len(s.causes), "n_concepts": len(s.concepts),
            "n_darstellung": len(s.darstellung),
            "sources": [q.title for q in s.sources],
            "competences": list(s.competences),
            "status": self.status, "source": self.source, "updated_at": self.updated_at,
        }


class SachverhaltStore(JsonStore[SachverhaltRecord]):
    model = SachverhaltRecord
    subdir = "sachverhalte"

    def list(self, *, status: str | None = None) -> list[SachverhaltRecord]:
        return self._list(where=lambda r: status is None or r.status == status,
                          sort_key=lambda r: r.id)

    def approved(self) -> list[SachverhaltRecord]:
        return self.list(status="approved")
