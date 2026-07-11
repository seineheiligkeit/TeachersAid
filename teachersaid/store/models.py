"""Review-queue data model. ONE item type with a `stage` discriminator so both
HITL stages share queue / status / feedback machinery.

The store holds only review items + an approved-material library — deliberately
no gradebook, no classroom state, no student PII (scope discipline).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..pipeline.plan import WorksheetPlan
from ..schema.worksheet import BundleRequest, LehrplanResolution, WorksheetContent


class Feedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    at: str
    decision: str  # approve | reject | request-changes
    note: str = ""


class RenderArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_pdf: str | None = None
    teacher_pdf: str | None = None
    homework_pdf: str | None = None
    preview_png: str | None = None  # student sheet, page 1 (dashboard preview)


class ReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    stage: str  # "brainstorm" | "content"
    status: str = "pending"  # pending | approved | rejected | changes_requested | generating
    source: str = "user"  # user | ai
    created_at: str = ""
    updated_at: str = ""
    title: str = ""
    note: str = ""  # brainstorm: the rough idea / rationale (free text)
    request: BundleRequest
    resolution: LehrplanResolution | None = None
    # idea-stage payload
    plan: WorksheetPlan | None = None
    # content-stage payload
    content: WorksheetContent | None = None
    artifacts: RenderArtifacts | None = None
    verify_problems: list[str] = Field(default_factory=list)
    verify_warnings: list[str] = Field(default_factory=list)
    parent_id: str | None = None  # content item -> its approved idea item
    feedback: list[Feedback] = Field(default_factory=list)
    error: str | None = None

    def n_tasks(self) -> int:
        from ..schema.enums import Role
        if not self.content:
            return 0
        return sum(1 for b in self.content.iter_blocks() if b.role == Role.TASK)

    def summary(self) -> dict:
        """A compact dict for the queue/status views (no heavy nested content)."""
        cov = gaps = tasks = None
        if self.content and self.content.nachweis:
            cov = sum(1 for c in self.content.nachweis.competence_coverage if c.covered)
            gaps = len(self.content.nachweis.gaps)
            tasks = self.n_tasks()
        anchor_mode = (
            self.content.anchor_mode if self.content is not None else self.request.anchor_mode
        )
        anchor_label = (
            self.content.nachweis.anchor_label
            if self.content is not None and self.content.nachweis is not None else None
        )
        return {
            "id": self.id,
            "stage": self.stage,
            "status": self.status,
            "source": self.source,
            "title": self.title,
            "note": self.note,
            "subject": self.request.subject,
            "klasse": self.request.klasse,
            "topic": self.request.topic_raw,
            "covered": cov,
            "gaps": gaps,
            "tasks": tasks,
            "anchor_mode": anchor_mode,
            "anchor_label": anchor_label,
            "n_feedback": len(self.feedback),
            "error": self.error,
            "updated_at": self.updated_at,
        }
