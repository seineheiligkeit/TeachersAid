"""JSON-file-backed store for Lernarrangements (schema v0.5) + their HITL review.

Parallel to the other stores (one JSON per record under RUNS_DIR/arrangements/,
idempotent `upsert` preserving review status). A record holds the assembled
`Lernarrangement` (its derived Nachweis/DepthProfile included), the rendered bundle
artifacts (orchestration PDF + per-role student/teacher PDFs under
RUNS_DIR/arrangements/<id>/), and any verify problems — everything the dashboard's
Arrangements tab needs to review one.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..config import RUNS_DIR
from ..schema.arrangement import Lernarrangement

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ArrangementArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    orchestration: str | None = None        # the teacher run-guide PDF
    roles: list[dict] = Field(default_factory=list)  # [{id,label,student,teacher}]


class ArrangementRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    arrangement: Lernarrangement
    status: str = "in_review"               # in_review | approved | rejected
    source: str = "ai"                      # ai | user | curated
    title: str = ""
    artifacts: ArrangementArtifacts | None = None
    verify_problems: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def summary(self) -> dict:
        m = self.arrangement.meta
        n = self.arrangement.nachweis
        cov = sum(1 for c in n.competence_coverage if c.covered) if n else None
        return {
            "id": self.id, "title": self.title or m.title, "subject": m.subject,
            "klasse": m.klasse, "format": m.format, "status": self.status,
            "source": self.source, "n_roles": len(self.arrangement.roles),
            "n_anchors": len(self.arrangement.competence_anchors),
            "minutes": self.arrangement.total_minutes(),
            "covered": cov, "gaps": len(n.gaps) if n else None,
            "problems": len(self.verify_problems), "updated_at": self.updated_at,
        }


class ArrangementStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else RUNS_DIR / "arrangements"
        self.root.mkdir(parents=True, exist_ok=True)
        self._counter = self.root / "_counter.txt"

    def next_id(self) -> str:
        with _LOCK:
            n = int(self._counter.read_text(encoding="utf-8") or "0") if self._counter.exists() else 0
            n += 1
            self._counter.write_text(str(n), encoding="utf-8")
        return f"a{n:04d}"

    def _path(self, rid: str) -> Path:
        return self.root / (rid.replace("/", "__") + ".json")

    def upsert(self, rec: ArrangementRecord) -> ArrangementRecord:
        with _LOCK:
            existing = self.get(rec.id)
            if existing is not None:
                rec.status = existing.status          # re-seeding never un-approves
                rec.created_at = existing.created_at
            else:
                rec.created_at = rec.created_at or _now()
            rec.updated_at = _now()
            self._path(rec.id).write_text(
                json.dumps(rec.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        return rec

    def save(self, rec: ArrangementRecord) -> ArrangementRecord:
        rec.updated_at = _now()
        self._path(rec.id).write_text(
            json.dumps(rec.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        return rec

    def get(self, rid: str) -> ArrangementRecord | None:
        p = self._path(rid)
        if not p.exists():
            return None
        return ArrangementRecord.model_validate_json(p.read_text(encoding="utf-8"))

    def set_status(self, rid: str, status: str) -> ArrangementRecord:
        rec = self.get(rid)
        if rec is None:
            raise KeyError(rid)
        rec.status = status
        return self.save(rec)

    def list(self, *, status: str | None = None) -> list[ArrangementRecord]:
        out: list[ArrangementRecord] = []
        for p in self.root.glob("*.json"):
            try:
                rec = ArrangementRecord.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if status and rec.status != status:
                continue
            out.append(rec)
        out.sort(key=lambda r: r.updated_at, reverse=True)
        return out
