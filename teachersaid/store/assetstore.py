"""JSON-file-backed store for the reusable asset library (Phase 4 #4).

The asset-as-reviewed-library for the two classes whose **durable artifact is a
file**: *decorative* (content-free, reusable — svg/code now, diffusion later) and
*sourced* (external + provenance). It runs parallel to the block library:
`AssetStore` mirrors `BlockStore` (one JSON per entry under RUNS_DIR/assets_lib/,
idempotent `upsert` preserving review status, status filters). The file itself
lives under .../files/.

Code-generated *content* assets are NOT here — they stay as `{generator, spec}`
specs on blocks (rebuilt on demand). This store is for the file-backed classes
that the media-policy gate routes to human review (`Documents/schema-roadmap`).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..schema.assets import Asset
from .base import JsonStore

KLASSES = ("decorative", "sourced")  # the file-backed asset classes


class LibraryAsset(BaseModel):
    """An asset whose durable artifact is a file, plus library metadata for review
    and reuse (tags). Wraps the schema `Asset` (role/medium/generator/spec/
    provenance/caption) the same way `LibraryBlock` wraps a `Block`."""
    model_config = ConfigDict(extra="forbid")
    id: str
    asset: Asset
    klass: str                          # "decorative" | "sourced"
    tags: list[str] = Field(default_factory=list)  # for reuse/search
    file: str | None = None             # path to the durable artifact (raster/svg/source)
    status: str = "in_review"           # in_review | approved | rejected
    source: str = "ai"                  # ai | user | curated
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        a = self.asset
        return {
            "id": self.id, "klass": self.klass, "role": a.role,
            "medium": str(a.medium), "generator": a.generator, "tags": self.tags,
            "caption": a.caption, "status": self.status, "source": self.source,
            "has_file": bool(self.file), "updated_at": self.updated_at,
        }


class AssetStore(JsonStore[LibraryAsset]):
    model = LibraryAsset
    subdir = "assets_lib"

    def __init__(self, root: Path | None = None):
        super().__init__(root)
        self.files_dir = self.root / "files"   # the durable artifacts live here
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def list(self, *, klass: str | None = None, status: str | None = None,
             tag: str | None = None) -> list[LibraryAsset]:
        return self._list(
            where=lambda a: (klass is None or a.klass == klass)
            and (status is None or a.status == status)
            and (tag is None or tag in a.tags),
            sort_key=lambda a: (a.klass, a.asset.role, a.id))

    def approved(self, *, tag: str | None = None) -> list[LibraryAsset]:
        """Approved, reusable assets — the kit the composer/teacher can draw on."""
        return self.list(status="approved", tag=tag)
