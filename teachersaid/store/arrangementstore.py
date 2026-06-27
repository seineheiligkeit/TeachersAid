"""JSON-file-backed store for Lernarrangements (schema v0.5) + their HITL review.

Parallel to the other stores (one JSON per record under RUNS_DIR/arrangements/,
idempotent `upsert` preserving review status). A record holds the assembled
`Lernarrangement` (its derived Nachweis/DepthProfile included), the rendered bundle
artifacts (orchestration PDF + per-role student/teacher PDFs under
RUNS_DIR/arrangements/<id>/), and any verify problems — everything the dashboard's
Arrangements tab needs to review one.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..schema.arrangement import Lernarrangement
from .base import JsonStore


class ArrangementArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    orchestration: str | None = None        # the teacher run-guide PDF
    roles: list[dict] = Field(default_factory=list)  # [{id,label,student,teacher}]


class ArrangementRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    arrangement: Lernarrangement
    status: str = "in_review"               # in_review | approved | rejected
    source: str = "ai"                      # ai | user | curated
    title: str = ""
    artifacts: ArrangementArtifacts | None = None
    verify_problems: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        m = self.arrangement.meta
        n = self.arrangement.nachweis
        cov = sum(1 for c in n.competence_coverage if c.covered) if n else None
        return {
            "id": self.id, "title": self.title or m.title, "subject": m.subject,
            "klasse": m.klasse, "format": m.format, "status": self.status,
            "source": self.source, "n_roles": len(self.arrangement.roles),
            "n_anchors": len(self.arrangement.competence_anchors),
            "minutes": self.arrangement.total_minutes(),
            "covered": cov, "gaps": len(n.gaps) if n else None,
            "problems": len(self.verify_problems), "updated_at": self.updated_at,
        }


class ArrangementStore(JsonStore[ArrangementRecord]):
    model = ArrangementRecord
    subdir = "arrangements"

    def next_id(self) -> str:
        return self._next_seq("a")

    def list(self, *, status: str | None = None) -> list[ArrangementRecord]:
        return self._list(where=lambda r: status is None or r.status == status,
                          sort_key=lambda r: r.updated_at, reverse=True)
