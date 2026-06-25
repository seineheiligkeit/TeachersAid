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


# --- GATE 1 entry: brainstorm / ideation ------------------------------------
def submit_brainstorm(
    store: ReviewStore, subject: str, klasse: int, topic: str, note: str = "",
    *, source: str = "user",
) -> ReviewItem:
    """A rough idea (user- or AI-produced): subject / Klasse / topic + a free-text
    note. No resolution or plan yet — those are produced at flesh_out()."""
    item = ReviewItem(
        id="", stage="brainstorm", source=source, status="pending",
        title=f"{subject} {klasse}. Kl. — {topic}",
        note=note,
        request=BundleRequest(subject=subject, klasse=klasse, topic_raw=topic),
    )
    return store.create(item)


def suggest_from_catalog(
    store: ReviewStore, subject: str, klasse: int
) -> list[ReviewItem]:
    """AI/Lehrplan suggestions: one brainstorm idea per Kompetenzbereich of the
    grade that isn't already represented anywhere in the queue/library."""
    from ..grounding import lehrplan_store as ls

    seen = {
        (i.request.subject.casefold(), i.request.klasse, i.request.topic_raw.casefold())
        for i in store.list() if i.request
    }
    out: list[ReviewItem] = []
    for kb in ls.grade_map(subject).get(klasse, []):
        if (subject.casefold(), klasse, kb.casefold()) in seen:
            continue
        out.append(submit_brainstorm(
            store, subject, klasse, kb, source="ai",
            note="Lehrplan-Vorschlag — Kompetenzbereich noch nicht ausgearbeitet.",
        ))
    return out


def approve_brainstorm(store: ReviewStore, item_id: str) -> ReviewItem:
    item = store.get(item_id)
    if item is None or item.stage != "brainstorm":
        raise KeyError(f"no brainstorm item '{item_id}'")
    item.status = "approved"
    store.append_feedback(item_id, "approve")
    return store.save(item)


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
    # Offline fallback: serve a curated master-library example (a hand-authored
    # content object) so the dashboard demos the full content→render→review loop
    # without an API key. With a key, the same flow generates fresh content.
    from ..library import find as find_example

    ex = find_example(res.subject, p.topic)
    if ex is not None:
        return ex.build()
    raise RuntimeError(
        "No ANTHROPIC_API_KEY and no master-library example for "
        f"{res.subject} / '{p.topic}'. Set a key to generate live, "
        "or add the example to teachersaid.library."
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


# --- GATE 1 approve -> flesh out into a content item ------------------------
def flesh_out(
    store: ReviewStore,
    brainstorm_id: str,
    *,
    generator: StructuredGenerator | None = None,
    today: date | None = None,
) -> ReviewItem:
    """Develop an approved brainstorm idea into a worksheet: resolve → plan →
    generate → verify → assemble(+derive) → render, landing a content item at
    Gate 2 for review. Offline, generation is served from the master library."""
    bs = store.get(brainstorm_id)
    if bs is None or bs.stage != "brainstorm":
        raise KeyError(f"no brainstorm item '{brainstorm_id}'")
    bs.status = "approved"
    bs.resolution = resolve(bs.request, today=today)
    bs.plan = plan(bs.resolution, bs.request.envelope, topic=bs.request.topic_raw)
    store.save(bs)
    notes = [f.note for f in bs.feedback if f.decision == "request-changes" and f.note]
    return _produce_content_item(store, bs, generator=generator, extra_notes=notes)


def compose_worksheet(
    store: ReviewStore,
    block_store,
    subject: str,
    klasse: int,
    topic: str,
    envelope: str = "doppelstunde",
    *,
    kompetenzbereich: str | None = None,
    today: date | None = None,
) -> ReviewItem:
    """Assemble a worksheet from approved library blocks (Phase 2) into a content
    item for Gate-2 review. Selection happens in pipeline/compose (by an explicit
    Kompetenzbereich when given, else by the topic); the existing assemble(+derive) /
    verify / render stages then run unchanged."""
    from .compose import compose

    display = (topic or "").strip() or kompetenzbereich or "Arbeitsblatt"
    item = ReviewItem(
        id="", stage="content", source="compose",
        title=f"{subject} {klasse}. Kl. — {display} (zusammengestellt)",
        request=BundleRequest(subject=subject, klasse=klasse, topic_raw=display, envelope=envelope),
    )
    store.create(item)
    try:
        content, res = compose(
            subject, klasse, topic, envelope,
            kompetenzbereich=kompetenzbereich, block_store=block_store, today=today,
        )
        item.resolution = res
        assemble(content, res)
        report = verify(content, res)
        item.artifacts = _render_all(item.id, content)
        item.content = content
        item.verify_problems = report.problems
        item.verify_warnings = report.warnings
        item.status = "pending"
        item.error = None
    except Exception as exc:  # noqa: BLE001 — surface as an item error, don't crash
        item.error = f"{type(exc).__name__}: {exc}"
        item.status = "pending"
    return store.save(item)


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
    if item.stage == "brainstorm":
        item.status = "changes_requested"
        return store.save(item)
    # content stage: regenerate with the accumulated feedback, re-queue for review
    notes = [f.note for f in item.feedback if f.decision == "request-changes" and f.note]
    idea = store.get(item.parent_id) if item.parent_id else item
    return _produce_content_item(
        store, idea, generator=generator, extra_notes=notes, existing=item
    )
