"""Demand queue (Track 2 #5, offline-first program) — the delivery loop's gap outlet.

Under the offline-first pivot (invariants §10) a request the corpus cannot serve is
answered with an *honest gap* — and that gap is worth keeping: it is the demand
signal that prioritises the next corpus campaign. A `DemandRecord` is one recorded
wish (subject × Klasse × topic/Kompetenzbereich × envelope); the Statistik tab lists
them next to the coverage planner, and a campaign marks them planned → fulfilled.

Deliberately tiny: no user identity, no free-form chat — a wish is a corpus-loop
work item, not a conversation (scope discipline: no classroom state, no PII).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .base import JsonStore, now

STATUSES = ("open", "planned", "fulfilled", "dismissed")


class DemandRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = ""
    status: str = "open"               # open | planned | fulfilled | dismissed
    subject: str
    klasse: int
    topic: str = ""
    kompetenzbereich: str | None = None
    envelope: str = "doppelstunde"
    note: str = ""                     # why delivery gapped (the honest reason)
    requested_via: str = "dashboard"   # dashboard | api | test
    fulfilled_by: str | None = None    # the content item that closed the wish
    created_at: str = ""
    updated_at: str = ""


class DemandStore(JsonStore[DemandRecord]):
    model = DemandRecord
    subdir = "demand"

    def create(self, rec: DemandRecord) -> DemandRecord:
        if not rec.id:
            rec.id = self._next_seq("d")
        rec.created_at = rec.created_at or now()
        return self._write(rec)

    def list(self, status: str | None = None) -> list[DemandRecord]:
        return self._list(
            where=lambda r: status is None or r.status == status,
            sort_key=lambda r: r.updated_at, reverse=True)
