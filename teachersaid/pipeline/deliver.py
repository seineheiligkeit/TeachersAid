"""The delivery loop (Track 2 #4 v1 + #5) — deterministic, LLM-free (invariants §10).

`deliver()` is the product's read path under the offline-first pivot, the retrieval
hierarchy in code:

    1. serve a **vetted worksheet** from the approved library (best match), else
    2. **compose** one from approved blocks (the existing `compose` → assemble →
       verify, no LLM anywhere), else
    3. an **honest gap** — recorded in the demand queue as the corpus loop's intake.

Delivery is *read-only against the corpus*: it never stages anything into the
review queue and never calls a generator; the only write is the demand record on a
gap. Inter-block coherence (the Track-2 hard problem) is deliberately NOT here yet —
this is the hierarchy + the gap outlet, so the loop exists end-to-end.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from ..grounding import lehrplan_store as ls
from ..schema.enums import Role
from ..schema.worksheet import LehrplanResolution, WorksheetContent
from ..store.demandstore import DemandRecord, DemandStore
from .assemble import assemble
from .compose import _angle_terms, compose
from .plan import _ENVELOPE_MINUTES
from .resolve import resolve_kompetenzbereich
from .verify import verify


class DeliveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str                                   # "library" | "composed" | "gap"
    note: str = ""
    item_id: str | None = None                  # library: the approved ReviewItem id
    title: str | None = None
    content: WorksheetContent | None = None     # composed: the assembled worksheet
    resolution: LehrplanResolution | None = None
    n_tasks: int = 0
    est_minutes: int = 0
    verify_warnings: list[str] = Field(default_factory=list)
    demand_id: str | None = None                # gap: the recorded wish


def _task_minutes(content: WorksheetContent) -> tuple[int, int]:
    tasks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    return len(tasks), sum(getattr(b, "est_minutes", 0) or 0 for b in tasks)


def _library_match(review_store, subject, klasse, topic, kompetenzbereich, envelope, today):
    """Best approved library worksheet for the request, or None. Scoring is
    deterministic: competence overlap with the requested KB (3× weight) + topic-term
    overlap with title/Kernfrage + how well the task minutes fit the envelope."""
    code = ls._code_for(subject)
    target_ids: set[str] = set()
    if kompetenzbereich:
        try:
            res = resolve_kompetenzbereich(subject, klasse, kompetenzbereich, today=today)
            target_ids = {c.id for c in res.competences}
        except Exception:
            target_ids = set()
    terms = _angle_terms(topic or "")
    budget = _ENVELOPE_MINUTES.get(envelope, 100)

    best, best_score = None, 0.0
    for it in review_store.library():
        if ls._code_for(it.request.subject) != code or it.request.klasse != klasse:
            continue
        if it.content is None:
            continue
        score = 0.0
        if target_ids:
            served = {s.competence_id for b in it.content.iter_blocks()
                      if b.role == Role.TASK for s in b.serves}
            overlap = len(served & target_ids)
            if not overlap:
                continue
            score += 3.0 * overlap
        if terms:
            hay = _angle_terms(f"{it.title} {it.content.meta.kernfrage or ''}")
            t_overlap = len(terms & hay)
            if not target_ids and not t_overlap:
                continue
            score += t_overlap
        if not target_ids and not terms:
            continue                      # nothing to match on — don't serve arbitrary sheets
        _n, mins = _task_minutes(it.content)
        score += 1.0 - min(abs(mins - budget) / budget, 1.0)
        if score > best_score:
            best, best_score = it, score
    return best


def deliver(
    subject, klasse, topic, envelope="doppelstunde",
    *, kompetenzbereich: str | None = None,
    review_store, block_store, demand_store: DemandStore | None = None,
    today: date | None = None,
) -> DeliveryResult:
    """Serve a request from the corpus: vetted sheet › composed › honest gap."""
    display = (topic or "").strip() or (kompetenzbereich or "").strip() or "Arbeitsblatt"

    hit = _library_match(review_store, subject, klasse, topic, kompetenzbereich, envelope, today)
    if hit is not None:
        n, mins = _task_minutes(hit.content)
        return DeliveryResult(
            mode="library", item_id=hit.id, title=hit.title, content=hit.content,
            n_tasks=n, est_minutes=mins,
            note=f"Geprüftes Arbeitsblatt „{hit.title}“ aus der Bibliothek (SME-freigegeben).")

    try:
        content, res = compose(subject, klasse, topic, envelope,
                               kompetenzbereich=kompetenzbereich,
                               block_store=block_store, today=today)
        assemble(content, res)
        report = verify(content, res)
        n, mins = _task_minutes(content)
        return DeliveryResult(
            mode="composed", content=content, resolution=res, title=content.meta.title,
            n_tasks=n, est_minutes=mins,
            verify_warnings=report.problems + report.warnings,
            note=f"Aus {n} freigegebenen Bausteinen zusammengestellt (~{mins} min, deterministisch).")
    except ValueError as exc:
        demand_id = None
        if demand_store is not None:
            rec = demand_store.create(DemandRecord(
                subject=subject, klasse=klasse, topic=(topic or "").strip(),
                kompetenzbereich=(kompetenzbereich or "").strip() or None,
                envelope=envelope, note=str(exc), requested_via="api"))
            demand_id = rec.id
        return DeliveryResult(
            mode="gap", demand_id=demand_id, title=display,
            note=(f"Ehrliche Lücke: {exc} Der Wunsch ist in der Wunschliste vorgemerkt und "
                  f"wird über eine Korpus-Kampagne (mit Review) erfüllt — nicht live generiert."))
