"""Shared JSON-file persistence — the one place the store boilerplate lives.

Every store is "one Pydantic record per JSON file under RUNS_DIR/<subdir>". This base
holds the machinery they all duplicated (path, read, write-with-timestamp, glob-list,
a sequential-id counter, and the idempotent status-preserving `upsert`); subclasses set
`model`/`subdir` and add their own *typed* query methods (`list(subject=…)` etc.).

Lifecycle deliberately varies and is NOT forced into one shape: the library stores
(Block/Asset/Arrangement/Dataset) `upsert` (re-seeding preserves review status), the
review store `create`s with a generated id, the feedback store `add`s append-only. Only
the genuinely shared parts are hoisted — forcing one `list()` signature or one lifecycle
on all six would be the wrong abstraction. This is also the seam a future SQLite backend
swaps behind (callers go through these methods, never touch files). See
`Documents/architecture-review.md`.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from ..config import RUNS_DIR

T = TypeVar("T", bound=BaseModel)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JsonStore(Generic[T]):
    """One-JSON-file-per-record store. Subclasses set `model` + `subdir`."""

    model: type[T]
    subdir: str

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else RUNS_DIR / self.subdir
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._counter = self.root / "_counter.txt"

    # --- file I/O ------------------------------------------------------------
    def _path(self, rec_id: str) -> Path:
        return self.root / (rec_id.replace("/", "__") + ".json")

    def _write(self, rec: T) -> T:
        if hasattr(rec, "updated_at"):
            rec.updated_at = now()
        self._path(rec.id).write_text(
            json.dumps(rec.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        return rec

    def get(self, rec_id: str) -> T | None:
        p = self._path(rec_id)
        if not p.exists():
            return None
        return self.model.model_validate_json(p.read_text(encoding="utf-8"))

    def _list(self, *, where: Callable[[T], bool] | None = None,
              sort_key: Callable | None = None, reverse: bool = False,
              pattern: str = "*.json") -> list[T]:
        out: list[T] = []
        for p in self.root.glob(pattern):
            try:
                rec = self.model.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if where is None or where(rec):
                out.append(rec)
        if sort_key is not None:
            out.sort(key=sort_key, reverse=reverse)
        return out

    # --- sequential ids ------------------------------------------------------
    def _next_seq(self, prefix: str, width: int = 4) -> str:
        with self._lock:
            n = int(self._counter.read_text(encoding="utf-8") or "0") if self._counter.exists() else 0
            n += 1
            self._counter.write_text(str(n), encoding="utf-8")
        return f"{prefix}{n:0{width}d}"

    # --- status lifecycle (library stores) -----------------------------------
    def save(self, rec: T) -> T:
        return self._write(rec)

    def upsert(self, rec: T) -> T:
        """Idempotent create-or-update preserving status + created_at, so re-seeding
        from a catalog never un-approves a reviewed record."""
        with self._lock:
            existing = self.get(rec.id)
            if existing is not None:
                rec.status = existing.status
                rec.created_at = existing.created_at
            else:
                rec.created_at = rec.created_at or now()
            return self._write(rec)

    def set_status(self, rec_id: str, status: str) -> T:
        rec = self.get(rec_id)
        if rec is None:
            raise KeyError(rec_id)
        rec.status = status
        return self.save(rec)
