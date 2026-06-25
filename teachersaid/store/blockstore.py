"""JSON-file-backed store for the master block library.

One LibraryBlock per JSON file under RUNS_DIR/blocks. `upsert` is idempotent by id
and preserves an existing block's review status (so re-seeding never un-approves).
The approved blocks are the library the composer will draw on.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..config import RUNS_DIR
from ..library.block import LibraryBlock

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BlockStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else RUNS_DIR / "blocks"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, block_id: str) -> Path:
        return self.root / (block_id.replace("/", "__") + ".json")

    def upsert(self, lb: LibraryBlock) -> LibraryBlock:
        """Create, or update content/metadata while preserving status + created_at."""
        with _LOCK:
            existing = self.get(lb.id)
            if existing is not None:
                lb.status = existing.status
                lb.created_at = existing.created_at
            else:
                lb.created_at = lb.created_at or _now()
            lb.updated_at = _now()
            self._path(lb.id).write_text(
                json.dumps(lb.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return lb

    def save(self, lb: LibraryBlock) -> LibraryBlock:
        lb.updated_at = _now()
        self._path(lb.id).write_text(
            json.dumps(lb.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return lb

    def get(self, block_id: str) -> LibraryBlock | None:
        p = self._path(block_id)
        if not p.exists():
            return None
        return LibraryBlock.model_validate_json(p.read_text(encoding="utf-8"))

    def set_status(self, block_id: str, status: str) -> LibraryBlock:
        lb = self.get(block_id)
        if lb is None:
            raise KeyError(block_id)
        lb.status = status
        return self.save(lb)

    def list(self, *, subject: str | None = None, status: str | None = None,
             role: str | None = None) -> list[LibraryBlock]:
        out: list[LibraryBlock] = []
        for p in self.root.glob("*.json"):
            try:
                lb = LibraryBlock.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if subject and lb.subject != subject:
                continue
            if status and lb.status != status:
                continue
            if role and lb.role != role:
                continue
            out.append(lb)
        out.sort(key=lambda b: (b.subject, b.kompetenzbereich or "", b.id))
        return out

    def approved(self) -> list[LibraryBlock]:
        return self.list(status="approved")
