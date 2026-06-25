"""JSON-file-backed review store (sufficient for the demo).

Each ReviewItem is one JSON file under RUNS_DIR/store; the approved-material
library is the set of content-stage items with status == approved.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..config import RUNS_DIR
from .models import Feedback, ReviewItem

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ReviewStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else RUNS_DIR / "store"
        self.root.mkdir(parents=True, exist_ok=True)
        self._counter_file = self.root / "_counter.txt"

    # --- ids -----------------------------------------------------------------
    def _next_id(self, stage: str) -> str:
        with _LOCK:
            n = 0
            if self._counter_file.exists():
                n = int(self._counter_file.read_text(encoding="utf-8") or "0")
            n += 1
            self._counter_file.write_text(str(n), encoding="utf-8")
        return f"{stage[:1]}{n:04d}"

    def _path(self, item_id: str) -> Path:
        return self.root / f"{item_id}.json"

    # --- crud ----------------------------------------------------------------
    def create(self, item: ReviewItem) -> ReviewItem:
        if not item.id:
            item.id = self._next_id(item.stage)
        item.created_at = item.created_at or _now()
        item.updated_at = _now()
        self._save(item)
        return item

    def _save(self, item: ReviewItem) -> None:
        item.updated_at = _now()
        self._path(item.id).write_text(
            json.dumps(item.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, item_id: str) -> ReviewItem | None:
        p = self._path(item_id)
        if not p.exists():
            return None
        return ReviewItem.model_validate_json(p.read_text(encoding="utf-8"))

    def save(self, item: ReviewItem) -> ReviewItem:
        self._save(item)
        return item

    def list(self, stage: str | None = None, status: str | None = None) -> list[ReviewItem]:
        items: list[ReviewItem] = []
        for p in self.root.glob("*.json"):
            try:
                it = ReviewItem.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if stage and it.stage != stage:
                continue
            if status and it.status != status:
                continue
            items.append(it)
        items.sort(key=lambda i: i.updated_at, reverse=True)
        return items

    def append_feedback(self, item_id: str, decision: str, note: str = "") -> ReviewItem:
        item = self.get(item_id)
        if item is None:
            raise KeyError(item_id)
        item.feedback.append(Feedback(at=_now(), decision=decision, note=note))
        self._save(item)
        return item

    def library(self) -> list[ReviewItem]:
        """Approved content-stage items = the representable-material library."""
        return self.list(stage="content", status="approved")

    def status_counts(self) -> dict:
        counts: dict[str, int] = {}
        for it in self.list():
            key = f"{it.stage}/{it.status}"
            counts[key] = counts.get(key, 0) + 1
        return counts
