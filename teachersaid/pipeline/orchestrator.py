"""Two-stage HITL orchestration tying on-demand + batch to the review gates.

    request → resolve → plan ─► [GATE 1 idea item] ─approve─►
        generate → verify → assemble(+derive) → render ─► [GATE 2 content item]
        ─approve─► representable-material library

request-changes at either gate re-enters here with feedback injected. Both entry
paths (on-demand request, batch competence-map walk) share everything after Resolve.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from .. import config
from ..demo import strahlung
from ..llm.client import StructuredGenerator
from ..rendering.homework import render_homework
from ..rendering.qa_raster import rasterise
from ..rendering.student_sheet import render_student_sheet
from ..rendering.teacher_guide import render_teacher_guide
from ..schema.worksheet import BundleRequest, LehrplanResolution
from ..store.models import RenderArtifacts, ReviewItem
from ..store.repository import ReviewStore
from .assemble import assemble
from .assets import build_asset
from .generate import generate_body
from .plan import WorksheetPlan, plan
from .resolve import resolve
from .verify import verify


# --- GATE 1 entry: idea-stage items -----------------------------------------
def submit_on_demand(
    store: ReviewStore, request: BundleRequest, *, today: date | None = None
) -> ReviewItem:
    res = resolve(request, today=today)
    p = plan(res, request.envelope, topic=request.topic_raw)
    item = ReviewItem(
        id="",
        stage="idea",
        source="on_demand",
        title=f"{request.subject} {request.klasse}. Kl. — {request.topic_raw}",
        request=request,
        resolution=res,
        plan=p,
        error=None if res.competences else "Keine Kompetenzen aufgelöst (Demo-Grenze).",
    )
    return store.create(item)


def submit_batch(
    store: ReviewStore, subject: str, klasse: int, *, today: date | None = None
) -> list[ReviewItem]:
    """Walk the grounded competence map: one candidate idea per Kompetenzbereich."""
    from ..grounding import lehrplan_store as ls

    comps = ls.competences_for(subject, klasse)
    kbs = sorted({c.kompetenzbereich for c in comps})
    out: list[ReviewItem] = []
    for kb in kbs:
        req = BundleRequest(subject=subject, klasse=klasse, topic_raw=kb)
        res = resolve(req, today=today)
        p = plan(res, "doppelstunde", topic=kb)
        out.append(
            store.create(
                ReviewItem(
                    id="", stage="idea", source="batch",
                    title=f"{subject} {klasse}. Kl. — {kb}",
                    request=req, resolution=res, plan=p,
                )
            )
        )
    return out


# --- generation (LLM or offline hero fallback) ------------------------------
def _has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _generate_content(
    p: WorksheetPlan,
    res: LehrplanResolution,
    *,
    generator: StructuredGenerator | None,
    extra_notes: list[str],
):
    if generator is not None or _has_key():
        return generate_body(p, res, generator=generator, extra_notes=extra_notes)
    # Offline fallback: the hand-authored hero, so the dashboard demos without a key.
    if res.subject == "Physik" and "strahlung" in p.topic.casefold():
        return strahlung.build_content()
    raise RuntimeError(
        "No ANTHROPIC_API_KEY and no offline content for this topic. "
        "Set a key to generate, or use the Strahlung hero."
    )


def _render_all(item_id: str, content) -> RenderArtifacts:
    out = config.RUNS_DIR / "store" / item_id
    # only code-generated (visual) assets render to images; audio/sourced assets
    # carry provenance but aren't embedded as pictures.
    assets = {
        a.id: build_asset(a, outdir=out / "assets")
        for a in content.assets
        if a.generator
    }
    student = render_student_sheet(content, out / "student.pdf", assets)
    teacher = render_teacher_guide(content, out / "teacher.pdf", assets)
    homework = render_homework(content, out / "homework.pdf", assets)
    preview_pages = rasterise(student, out_dir=out / "raster")
    return RenderArtifacts(
        student_pdf=str(student),
        teacher_pdf=str(teacher),
        homework_pdf=str(homework),
        preview_png=str(preview_pages[0]) if preview_pages else None,
    )


# --- GATE 1 approve -> generate -> GATE 2 content item ----------------------
def begin_idea_approval(store: ReviewStore, item_id: str) -> ReviewItem:
    """Mark the idea approved and create a 'generating' placeholder content item.
    Returns immediately; call fill_content_item() (e.g. in a background task)."""
    idea = store.get(item_id)
    if idea is None or idea.stage != "idea":
        raise KeyError(f"no idea item '{item_id}'")
    idea.status = "approved"
    store.append_feedback(item_id, "approve")
    store.save(idea)
    placeholder = ReviewItem(
        id="", stage="content", source=idea.source, status="generating",
        title=idea.title, request=idea.request, resolution=idea.resolution,
        plan=idea.plan, parent_id=idea.id,
    )
    return store.create(placeholder)


def fill_content_item(
    store: ReviewStore,
    content_id: str,
    *,
    generator: StructuredGenerator | None = None,
) -> ReviewItem:
    """Run generate→verify→assemble→render for a placeholder content item."""
    content_item = store.get(content_id)
    if content_item is None or content_item.stage != "content":
        raise KeyError(f"no content item '{content_id}'")
    idea = store.get(content_item.parent_id) if content_item.parent_id else content_item
    notes = [f.note for f in idea.feedback if f.decision == "request-changes" and f.note]
    notes += [f.note for f in content_item.feedback if f.decision == "request-changes" and f.note]
    return _produce_content_item(
        store, idea, generator=generator, extra_notes=notes, existing=content_item
    )


def approve_idea(
    store: ReviewStore,
    item_id: str,
    *,
    generator: StructuredGenerator | None = None,
) -> ReviewItem:
    """Synchronous convenience: approve + generate in one call (tests/CLI)."""
    placeholder = begin_idea_approval(store, item_id)
    return fill_content_item(store, placeholder.id, generator=generator)


def _produce_content_item(
    store: ReviewStore,
    idea: ReviewItem,
    *,
    generator: StructuredGenerator | None,
    extra_notes: list[str],
    existing: ReviewItem | None = None,
) -> ReviewItem:
    content_item = existing or ReviewItem(
        id="", stage="content", source=idea.source,
        title=idea.title, request=idea.request, resolution=idea.resolution,
        plan=idea.plan, parent_id=idea.id,
    )
    if not content_item.id:
        store.create(content_item)
    try:
        content = _generate_content(
            idea.plan, idea.resolution, generator=generator, extra_notes=extra_notes
        )
        assemble(content, idea.resolution)
        report = verify(content, idea.resolution, plan=idea.plan)
        artifacts = _render_all(content_item.id, content)
        content_item.content = content
        content_item.artifacts = artifacts
        content_item.verify_problems = report.problems
        content_item.verify_warnings = report.warnings
        content_item.status = "pending"
        content_item.error = None
    except Exception as exc:  # noqa: BLE001 — surface as an item error, don't crash
        content_item.error = f"{type(exc).__name__}: {exc}"
        content_item.status = "pending"
    return store.save(content_item)


# --- GATE 2 + feedback loop -------------------------------------------------
def approve_content(store: ReviewStore, item_id: str) -> ReviewItem:
    item = store.get(item_id)
    if item is None or item.stage != "content":
        raise KeyError(f"no content item '{item_id}'")
    item.status = "approved"  # enters the representable-material library
    store.append_feedback(item_id, "approve")
    return store.save(item)


def reject(store: ReviewStore, item_id: str, note: str = "") -> ReviewItem:
    item = store.get(item_id)
    if item is None:
        raise KeyError(item_id)
    item.status = "rejected"
    store.append_feedback(item_id, "reject", note)
    return store.save(item)


def request_changes(
    store: ReviewStore,
    item_id: str,
    note: str,
    *,
    generator: StructuredGenerator | None = None,
) -> ReviewItem:
    item = store.get(item_id)
    if item is None:
        raise KeyError(item_id)
    store.append_feedback(item_id, "request-changes", note)
    item = store.get(item_id)
    if item.stage == "idea":
        item.status = "changes_requested"
        return store.save(item)
    # content stage: regenerate with the accumulated feedback, re-queue for review
    notes = [f.note for f in item.feedback if f.decision == "request-changes" and f.note]
    idea = store.get(item.parent_id) if item.parent_id else item
    return _produce_content_item(
        store, idea, generator=generator, extra_notes=notes, existing=item
    )
