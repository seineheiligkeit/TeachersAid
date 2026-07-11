"""JSON-file-backed store for the annotated-text library (HITL review).

Parallel to `DatasetStore`/`AssetStore`: each curated `AnnotatedText` is staged as a
reviewable `TextRecord` so a human vets the text, its rights, and its annotations before
content derives from it. `upsert` preserves review status (re-seeding never un-approves).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..schema.texts import AnnotatedText
from .base import JsonStore


class TextRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: AnnotatedText
    status: str = "in_review"           # in_review | approved | rejected
    source: str = "curated"
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        t = self.text
        s = t.source                        # None for a constructed Realie (no source/rights)
        return {
            "id": self.id, "title": t.title, "author": s.author if s else "—",
            "genre": t.genre, "klasse": t.klasse, "subject": t.subject, "medium": t.medium,
            "origin": t.origin, "cefr": t.cefr, "scene": t.scene,   # Realien tags
            "backdrop_asset": t.backdrop_asset,
            "rights_basis": s.rights_basis if s else None,
            "author_death_year": s.author_death_year if s else None,
            "attribution": s.attribution if s else ("Eigenproduktion (konstruiert)"
                                                    if t.origin == "constructed" else "—"),
            "repository": s.repository if s else None,
            "url": s.url if s else None, "n_lines": t.line_count(), "n_annotations": len(t.annotations),
            "status": self.status, "source": self.source, "updated_at": self.updated_at,
        }


class TextStore(JsonStore[TextRecord]):
    model = TextRecord
    subdir = "texts"

    def list(self, *, status: str | None = None) -> list[TextRecord]:
        return self._list(where=lambda r: status is None or r.status == status,
                          sort_key=lambda r: r.id)

    def approved(self) -> list[TextRecord]:
        return self.list(status="approved")
