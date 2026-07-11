"""JSON store for curated historical image sources (the sixth asset class)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ..schema.image_sources import ImageSource
from .base import JsonStore


class ImageSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    image_source: ImageSource
    file: str
    status: str = "in_review"
    source: str = "curated"
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        image = self.image_source
        ref = image.source
        return {
            "id": self.id,
            "title": image.title,
            "subject": image.subject,
            "klasse": image.klasse,
            "creator": ref.creator,
            "repository": ref.repository,
            "work_rights": ref.work_rights.basis,
            "reproduction_rights": ref.reproduction_rights.basis,
            "attribution": ref.attribution,
            "description_url": ref.description_url,
            "width": ref.width,
            "height": ref.height,
            "n_annotations": len(image.annotations),
            "related_sachverhalt_id": image.related_sachverhalt_id,
            "related_text_id": image.related_text_id,
            "file": self.file,
            "status": self.status,
            "source": self.source,
            "updated_at": self.updated_at,
        }


class ImageSourceStore(JsonStore[ImageSourceRecord]):
    model = ImageSourceRecord
    subdir = "image_sources"

    def __init__(self, root: Path | None = None):
        super().__init__(root)
        self.files_dir = self.root / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def list(self, *, status: str | None = None) -> list[ImageSourceRecord]:
        return self._list(
            where=lambda r: status is None or r.status == status,
            sort_key=lambda r: r.id,
        )

    def approved(self) -> list[ImageSourceRecord]:
        return self.list(status="approved")
