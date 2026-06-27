"""JSON-file-backed review store (sufficient for the demo).

Each ReviewItem is one JSON file under RUNS_DIR/store; the approved-material library is
the set of content-stage items with status == approved. Unlike the library stores it
`create`s with a generated, stage-prefixed id and then `save`s mutations (no
status-preserving upsert), so it keeps its own lifecycle on the shared JsonStore base.
"""

from __future__ import annotations

from .base import JsonStore, now
from .models import Feedback, ReviewItem


class ReviewStore(JsonStore[ReviewItem]):
    model = ReviewItem
    subdir = "store"

    def create(self, item: ReviewItem) -> ReviewItem:
        if not item.id:
            item.id = self._next_seq(item.stage[:1])
        item.created_at = item.created_at or now()
        return self._write(item)

    def list(self, stage: str | None = None, status: str | None = None) -> list[ReviewItem]:
        return self._list(
            where=lambda i: (stage is None or i.stage == stage)
            and (status is None or i.status == status),
            sort_key=lambda i: i.updated_at, reverse=True)

    def append_feedback(self, item_id: str, decision: str, note: str = "") -> ReviewItem:
        item = self.get(item_id)
        if item is None:
            raise KeyError(item_id)
        item.feedback.append(Feedback(at=now(), decision=decision, note=note))
        return self._write(item)

    def library(self) -> list[ReviewItem]:
        """Approved content-stage items = the representable-material library."""
        return self.list(stage="content", status="approved")

    def status_counts(self) -> dict:
        counts: dict[str, int] = {}
        for it in self.list():
            key = f"{it.stage}/{it.status}"
            counts[key] = counts.get(key, 0) + 1
        return counts
