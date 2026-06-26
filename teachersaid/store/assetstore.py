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

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..config import RUNS_DIR
from ..schema.assets import Asset

_LOCK = threading.Lock()
KLASSES = ("decorative", "sourced")  # the file-backed asset classes


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


class AssetStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else RUNS_DIR / "assets_lib"
        self.files_dir = self.root / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, asset_id: str) -> Path:
        return self.root / (asset_id.replace("/", "__") + ".json")

    def upsert(self, la: LibraryAsset) -> LibraryAsset:
        """Create, or update content/metadata while preserving status + created_at
        (so re-seeding the kit never un-approves a reviewed asset)."""
        with _LOCK:
            existing = self.get(la.id)
            if existing is not None:
                la.status = existing.status
                la.created_at = existing.created_at
            else:
                la.created_at = la.created_at or _now()
            la.updated_at = _now()
            self._path(la.id).write_text(
                json.dumps(la.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return la

    def save(self, la: LibraryAsset) -> LibraryAsset:
        la.updated_at = _now()
        self._path(la.id).write_text(
            json.dumps(la.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return la

    def get(self, asset_id: str) -> LibraryAsset | None:
        p = self._path(asset_id)
        if not p.exists():
            return None
        return LibraryAsset.model_validate_json(p.read_text(encoding="utf-8"))

    def set_status(self, asset_id: str, status: str) -> LibraryAsset:
        la = self.get(asset_id)
        if la is None:
            raise KeyError(asset_id)
        la.status = status
        return self.save(la)

    def list(self, *, klass: str | None = None, status: str | None = None,
             tag: str | None = None) -> list[LibraryAsset]:
        out: list[LibraryAsset] = []
        for p in self.root.glob("*.json"):
            try:
                la = LibraryAsset.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if klass and la.klass != klass:
                continue
            if status and la.status != status:
                continue
            if tag and tag not in la.tags:
                continue
            out.append(la)
        out.sort(key=lambda a: (a.klass, a.asset.role, a.id))
        return out

    def approved(self, *, tag: str | None = None) -> list[LibraryAsset]:
        """Approved, reusable assets — the kit the composer/teacher can draw on."""
        return self.list(status="approved", tag=tag)
