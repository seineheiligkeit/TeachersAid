"""JSON-file-backed store for the master block library.

One LibraryBlock per JSON file under RUNS_DIR/blocks. `upsert` (from JsonStore) is
idempotent by id and preserves an existing block's review status (so re-seeding never
un-approves). The approved blocks are the library the composer draws on.
"""

from __future__ import annotations

from ..library.block import LibraryBlock
from .base import JsonStore


class BlockStore(JsonStore[LibraryBlock]):
    model = LibraryBlock
    subdir = "blocks"

    def list(self, *, subject: str | None = None, status: str | None = None,
             role: str | None = None) -> list[LibraryBlock]:
        return self._list(
            where=lambda b: (subject is None or b.subject == subject)
            and (status is None or b.status == status)
            and (role is None or b.role == role),
            sort_key=lambda b: (b.subject, b.kompetenzbereich or "", b.id))

    def approved(self) -> list[LibraryBlock]:
        return self.list(status="approved")
