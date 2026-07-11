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
from ..llm.client import StructuredGenerator, default_generator
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
        if a.generator and not a.generator.startswith("audio:")  # audio isn't a PDF image
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
    generator: StructuredGenerator | None = None,
    today: date | None = None,
) -> ReviewItem:
    """Assemble a worksheet from approved library blocks (Phase 2) into a content
    item for Gate-2 review. Selection happens in pipeline/compose (by an explicit
    Kompetenzbereich when given, else by the topic). When an LLM is available
    (`generator` injected or an API key set) an optional **framing pass** (Phase 3e)
    writes a coherent Kernfrage + intro + transitions around the vetted blocks; offline
    the deterministic template framing stands. assemble(+derive) / verify / render then
    run unchanged."""
    from .compose import compose
    from .frame import frame_composition

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
        if generator is not None or _has_key():
            frame_composition(content, generator=generator or default_generator())
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


def stage_worksheet(
    store: ReviewStore, content, res: LehrplanResolution, *,
    source: str = "curated", title: str | None = None,
) -> ReviewItem:
    """Stage a PRE-BUILT, curated `WorksheetContent` as a Gate-2 content item (the
    library-flagship analogue of compose/ingest, for hand-authored examples like the
    History flagship). assemble(+derive) / verify / render run unchanged; the rights gate
    + prose gate ride inside verify, so a curated worksheet is held to the same bar."""
    item = ReviewItem(
        id="", stage="content", source=source,
        title=title or content.meta.title,
        request=BundleRequest(subject=content.meta.subject, klasse=content.meta.klasse,
                              topic_raw=content.meta.title),
        resolution=res,
    )
    store.create(item)
    try:
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


def compose_variants(store: ReviewStore, template_id: str, n: int = 6,
                     *, ramp: bool = False, today: date | None = None) -> ReviewItem:
    """Stage a parametric Maths worksheet (N correct-by-construction variants of a curated
    template) as a content item for Gate-2 review. The maths is computed (sympy), never
    authored, so every variant is right and carries its Rechenweg."""
    from ..library.templates import find_template, variant_worksheet

    t = find_template(template_id)
    if t is None:
        raise KeyError(f"no parametric template '{template_id}'")
    item = ReviewItem(
        id="", stage="content", source="variants",
        title=f"{t.subject} {t.klasse}. Kl. — {t.title or t.id} ({n} Varianten"
              f"{' · ansteigend' if ramp else ''})",
        request=BundleRequest(subject=t.subject, klasse=t.klasse, topic_raw=t.title or t.id),
    )
    store.create(item)
    try:
        content, res = variant_worksheet(t, n, ramp=ramp, today=today)
        item.resolution = res
        assemble(content, res)
        report = verify(content, res)
        item.artifacts = _render_all(item.id, content)
        item.content = content
        item.verify_problems = report.problems
        item.verify_warnings = report.warnings
        item.status = "pending"
        item.error = None
    except Exception as exc:  # noqa: BLE001
        item.error = f"{type(exc).__name__}: {exc}"
        item.status = "pending"
    return store.save(item)


def _check_provenance_rights(content, today_year: int) -> list[str]:
    """The expression-provenance ingest gate (History/GPB): every block that embeds
    source-derived wording (`adapted`/`quoted`) must rest on a redistributable/PD-clear
    basis (or a short quote under Zitatrecht). `original`/facts-only blocks are always clear.
    Returns a list of `<block_id>: <reason>` problems — non-empty blocks staging."""
    out: list[str] = []
    for b in content.iter_blocks():
        prov = getattr(b, "provenance", None)
        if prov is None:
            continue
        ok, reasons = prov.rights_gate(today_year)
        if not ok:
            out += [f"{b.id}: {r}" for r in reasons]
    return out


def ingest_generated(
    store: ReviewStore,
    block_store,
    subject: str,
    klasse: int,
    *,
    kompetenzbereich: str | None = None,
    scope_label: str | None = None,
    title: str,
    kernfrage: str,
    body,
    render: bool = True,
    today: date | None = None,
) -> tuple[ReviewItem, int]:
    """Land an LLM-generated worksheet body (a `GenWorksheetBody` or its dict) as a
    pending content item, and harvest its blocks into the block library (pending) —
    but only if it verifies clean. Reuses the real generation seam
    (`body_to_canonical` → assemble → verify → render), so the catalog, the subject
    model, and the verify rules gatekeep correctness. Returns (item, n_blocks_harvested).

    Anchor the resolution either to a `kompetenzbereich` (content-KB subjects like
    Physik/Mathe — focused coverage) or, when none is given, to the whole grade
    (strand-KB subjects like Biologie/Chemie, whose theme lives in the
    Anwendungsbereiche); `scope_label` is the human theme shown in the label.

    This is the breadth-push backbone: subagents generate the body; this validates and
    stages it for the two-stage HITL review (a competence id, kind, or dimension the
    model invented surfaces as an error/verify-problem here, not as a silent bad block)."""
    from ..grounding import lehrplan_store as ls
    from ..library.block import harvest
    from ..schema.generation_views import GenWorksheetBody, body_to_canonical
    from ..schema.worksheet import WorksheetMeta
    from .resolve import resolve_grade, resolve_kompetenzbereich

    stufe = ls.stufe_for_klasse(klasse)  # Klasse fixes the stage (1–4 / 5–8)
    if kompetenzbereich:
        res = resolve_kompetenzbereich(subject, klasse, kompetenzbereich, today=today)
    else:
        res = resolve_grade(subject, klasse, today=today)
    model = ls.get_subject_model(subject, stufe)
    if model is None:
        raise ValueError(f"no subject model for '{subject}' ({stufe})")
    label = kompetenzbereich or scope_label or f"{klasse}. Klasse"

    item = ReviewItem(
        id="", stage="content", source="generated",
        title=f"{subject} {klasse}. Kl. — {title} (generiert)",
        request=BundleRequest(subject=subject, klasse=klasse, topic_raw=title),
        resolution=res,
    )
    store.create(item)
    try:
        gb = body if isinstance(body, GenWorksheetBody) else GenWorksheetBody.model_validate(body)
        # A worksheet may legitimately serve competences across KBs (strand subjects like
        # Sport/Musik); if the chosen KB is too narrow but every serve is grade-valid,
        # widen the resolution to the whole grade rather than flag a false coverage error.
        if kompetenzbereich:
            served = {s.competence_id for sec in gb.sections for b in sec.blocks
                      for s in getattr(b, "serves", [])}
            if served - {c.id for c in res.competences}:
                from .resolve import resolve_grade
                gres = resolve_grade(subject, klasse, today=today)
                if served <= {c.id for c in gres.competences}:
                    res = gres
                    item.resolution = res
        meta = WorksheetMeta(
            title=title, subtitle="LLM-Entwurf — Erstprüfung",
            subject=subject, stufe=stufe, klasse=klasse,
            kernfrage=kernfrage, fassung=res.fassung,
            lehrplan_label=f"{subject} · {klasse}. Klasse · {label}",
        )
        content = body_to_canonical(gb, meta=meta, subject_model=model)
        # expression-provenance RIGHTS gate (History/GPB): refuse to stage a worksheet that
        # embeds non-clear source wording — the select-never-author discipline applied to
        # copyright (compliance is legal, not cosmetic), mirroring ingest_text's rights check.
        rights_problems = _check_provenance_rights(content, (today or date.today()).year)
        if rights_problems:
            raise ValueError("rights: eingebettete Quelle nicht nachnutzbar — "
                             + "; ".join(rights_problems))
        # ground data_source figures FIRST so their real values are filled before
        # build_asset is called (climate/population diagrams need temp/precip/etc.)
        from .data_ground import ground_data
        ground_data(content)
        # validate any LLM-requested assets: allowed recipe + it actually builds
        # (a bad/invented generator or spec surfaces as an error, never a silent block)
        if content.assets:
            from .assets import GENERATION_RECIPES, build_asset
            adir = config.RUNS_DIR / "store" / item.id / "assets"
            for a in content.assets:
                if a.generator not in GENERATION_RECIPES:
                    raise ValueError(
                        f"asset '{a.id}': generator {a.generator!r} not in the allowed recipe library"
                    )
                build_asset(a, outdir=adir)
        assemble(content, res)
        report = verify(content, res)
        # breadth mode renders no PDFs — blocks are the unit, inspected structurally
        item.artifacts = _render_all(item.id, content) if render else None
        item.content = content
        item.verify_problems = report.problems
        item.verify_warnings = report.warnings
        item.status = "pending"
        item.error = None
    except Exception as exc:  # noqa: BLE001 — surface as an item error, don't crash the batch
        item.error = f"{type(exc).__name__}: {exc}"
        item.status = "pending"
    store.save(item)

    harvested = 0
    if item.error is None and not (item.verify_problems or []):
        for lb in harvest(item.content, example_key=item.id):
            lb.status = "in_review"  # pending block review
            block_store.upsert(lb)
            harvested += 1
    return item, harvested


def ingest_scope_variant(
    block_store, original_id: str, scope: str, body_task, *, today: date | None = None
) -> tuple[object, list[str]]:
    """Validate a generated task-block **scope variant** and store it as a LibraryBlock
    tagged with the original block's id as `family` + the given `scope` (Phase 3a). Also
    stamps the original block's `family`, so the trio (compact/standard/extended) is one
    family the composer picks from by envelope. Reuses the verify seam; returns
    (LibraryBlock | None, problems) — a bad variant is never stored.

    `body_task` is a `GenTaskBlock` (or its dict): the same competence/kind/dimensions/
    cognitive_level as the original, but more/less content-rich + adjusted est_minutes."""
    from ..grounding import lehrplan_store as ls
    from ..library.block import LibraryBlock
    from ..schema.generation_views import GenTaskBlock, _task_to_canonical
    from ..schema.worksheet import Baustein, WorksheetContent, WorksheetMeta
    from .resolve import resolve_grade

    orig = block_store.get(original_id)
    if orig is None:
        return None, [f"unknown block '{original_id}'"]
    model = ls.get_subject_model(orig.subject)
    res = resolve_grade(orig.subject, orig.klasse, today=today)
    try:
        task = _task_to_canonical(
            body_task if isinstance(body_task, GenTaskBlock) else GenTaskBlock.model_validate(body_task)
        )
    except Exception as exc:  # noqa: BLE001
        return None, [f"schema: {type(exc).__name__}: {exc}"]
    # validate the single block through the real seam (kinds/dims/serves/level)
    content = WorksheetContent(
        meta=WorksheetMeta(title="(variant)", subject=orig.subject, stufe="Unterstufe",
                           klasse=orig.klasse, fassung=res.fassung, lehrplan_label=""),
        subject_model=model, sections=[Baustein(id="v", title="v", blocks=[task])],
    )
    assemble(content, res)
    report = verify(content, res)
    if report.problems:
        return None, report.problems

    lb = LibraryBlock(
        id=f"{original_id}#{scope}", block=task, role="task", kind=task.kind,
        subject=orig.subject, klasse=orig.klasse, kompetenzbereich=orig.kompetenzbereich,
        competences=[s.competence_id for s in task.serves], cognitive_level=task.cognitive_level,
        dimensions=list(task.dimensions or []), modality=getattr(task, "modality", "printable") or "printable",
        scope=scope, family=original_id, status="in_review",
        provenance=f"variant:{original_id}", source="ai",
    )
    block_store.upsert(lb)
    if orig.family != original_id:        # group the original (standard) with its variants
        orig.family = original_id
        block_store.save(orig)
    return lb, []


def ingest_asset(
    asset_store, asset, *, klass: str, tags=None, source: str = "ai",
    status: str = "in_review", file=None,
):
    """Bring a file-backed asset (decorative or sourced) into the asset library
    (Phase 4 #4). Runs the media-policy gate first — a decorative asset must be
    content-free; a sourced one must carry vetted rights — then materialises the
    durable file (built from the spec for an svg:/diffusion: generator, or copied
    in for a sourced external file) and stores a LibraryAsset for review + reuse."""
    import shutil

    from ..store.assetstore import KLASSES, LibraryAsset
    from .media_policy import check_asset

    if klass not in KLASSES:
        raise ValueError(f"unknown asset class {klass!r} (expected one of {KLASSES})")
    problems, _ = check_asset(asset)
    if problems:
        raise ValueError("media policy: " + "; ".join(problems))

    dest = None
    if file is not None:                       # sourced: copy the provided file in
        src = Path(file)
        dest = asset_store.files_dir / f"{asset.id}{src.suffix or '.bin'}"
        shutil.copyfile(src, dest)
    elif asset.generator:                      # decorative/diffusion: build from the spec
        build_asset(asset, outdir=asset_store.files_dir)
        dest = asset_store.files_dir / f"{asset.id}.png"

    la = LibraryAsset(
        id=asset.id, asset=asset, klass=klass, tags=list(tags or []),
        file=str(dest) if dest else None, source=source, status=status,
    )
    return asset_store.upsert(la)


def ingest_dataset(dataset_store, dataset, *, source: str = "curated",
                   status: str = "in_review"):
    """Stage a curated grounded-facts dataset for HITL review (the data-layer analogue
    of ingest_asset). Runs the licence/attribution gate first — a dataset whose values
    we *embed* must carry a recorded redistributable licence + attribution, the
    *select-never-author* rule applied to the licence itself — then stores it."""
    from ..store.datasetstore import DatasetRecord

    src = dataset.source
    if not src.attribution:
        raise ValueError(f"dataset {dataset.id}: missing source.attribution (citation string)")
    if not src.redistributable:
        raise ValueError(
            f"dataset {dataset.id}: licence not marked redistributable — embed values only "
            f"under a recorded redistributable licence (CC BY/equiv.); otherwise reference-only")
    rec = DatasetRecord(id=dataset.id, dataset=dataset, source=source, status=status)
    return dataset_store.upsert(rec)


def seed_datasets(dataset_store=None, *, status: str = "in_review"):
    """Stage every dataset in grounding/data/ into the review queue (cf. seed_blocks)."""
    from ..grounding import data_store as ds
    from ..store.datasetstore import DatasetStore

    store = dataset_store or DatasetStore()
    out = []
    for dataset in ds.list_datasets():
        out.append(ingest_dataset(store, dataset, status=status))
    return out


def ingest_text(text_store, annotated_text, *, source: str = "curated",
                status: str = "in_review", today: date | None = None):
    """Stage an annotated authentic text for HITL review. Runs the RIGHTS gate first —
    a text may only be redistributed on a clear basis (PD by the AT 70-Jahre-p.m.a. rule,
    or CC) — the select-never-author discipline applied to copyright (per the roadmap's
    PD-work-≠-PD-reproduction / AT-not-US caution)."""
    from ..store.textstore import TextRecord

    # A constructed Realie (invented-coherent fiction, no source) rides no rights gate — there is
    # nothing to clear (Documents/realien-design.md §9). Only a sourced/adapted text must clear.
    if annotated_text.source is not None:
        year = (today or date.today()).year
        ok, reasons = annotated_text.source.is_clear(year)
        if not ok:
            raise ValueError(f"rights: {annotated_text.id} not clear to redistribute — "
                             + "; ".join(reasons))
    # Realien: the internal-consistency lint (a scan answer can't cite data the Realie lacks).
    if annotated_text.scene is not None or annotated_text.cefr is not None or annotated_text.facts:
        from ..pipeline.realie_lint import lint as _realie_lint
        problems, _warnings = _realie_lint(annotated_text)
        if problems:
            raise ValueError(f"Realie {annotated_text.id}: interne Inkonsistenz — "
                             + "; ".join(problems))
    rec = TextRecord(id=annotated_text.id, text=annotated_text, source=source, status=status)
    return text_store.upsert(rec)


def seed_texts(text_store=None, *, status: str = "in_review", today: date | None = None):
    """Stage the curated annotated texts (library/texts.py) for review (cf. seed_datasets)."""
    from ..library.texts import ANNOTATED_TEXTS
    from ..store.textstore import TextStore

    store = text_store or TextStore()
    return [ingest_text(store, t, status=status, today=today) for t in ANNOTATED_TEXTS]


def compose_text_worksheet(store: ReviewStore, text_store, text_id: str,
                           *, today: date | None = None) -> ReviewItem:
    """Stage a worksheet derived from an annotated text as a content item for Gate-2
    review. Tasks' answers come from the vetted annotations (correct by curation)."""
    from ..pipeline.text_tasks import build_worksheet

    rec = text_store.get(text_id)
    if rec is None:
        raise KeyError(f"no annotated text '{text_id}'")
    at = rec.text
    item = ReviewItem(
        id="", stage="content", source="text",
        title=f"{at.subject} {at.klasse}. Kl. — {at.title}",
        request=BundleRequest(subject=at.subject, klasse=at.klasse, topic_raw=at.title),
    )
    store.create(item)
    try:
        content, res = build_worksheet(at, today=today)
        item.resolution = res
        assemble(content, res)
        report = verify(content, res)
        item.artifacts = _render_all(item.id, content)
        item.content = content
        item.verify_problems = report.problems
        item.verify_warnings = report.warnings
        item.status = "pending"
        item.error = None
    except Exception as exc:  # noqa: BLE001
        item.error = f"{type(exc).__name__}: {exc}"
        item.status = "pending"
    return store.save(item)


def ingest_sachverhalt(sachverhalt_store, sachverhalt, *, source: str = "curated",
                       status: str = "in_review"):
    """Stage a curated Sachverhalt for HITL review. Runs the FACTS gate first: at least one
    `role="facts"` source must be recorded (mandatory-internal, so each fact is fact-checked
    at the gate), and the entity-lint must be clean (every year in the Darstellung appears in
    the fact-set). The select-never-author discipline applied to a content module — numbers
    are guaranteed; the prose is a projection over the frozen facts (`invariants.md` §3)."""
    from ..pipeline.entity_lint import check_module
    from ..pipeline.sachverhalt_lint import lint
    from ..store.sachverhaltstore import SachverhaltRecord

    if not sachverhalt.facts_sources():
        raise ValueError(
            f"Sachverhalt {sachverhalt.id}: keine role='facts'-Quelle — jeder Sachverhalt "
            f"braucht eine recherchierte, prüfbare Faktenquelle (Pflicht-intern).")
    problems, _warnings = lint(sachverhalt)
    if problems:
        raise ValueError(f"Sachverhalt {sachverhalt.id}: Entity-Lint — " + "; ".join(problems))
    # Wave C2 corpus-consistency HARD checks: a linked entity_id must exist in the registry
    # and a linked event's year must not contradict it (grounding/entities). Advisory
    # link-suggestions are surfaced by tools/entity_check.py, not blocked here.
    reg_problems, _reg_warnings = check_module(sachverhalt)
    if reg_problems:
        raise ValueError(
            f"Sachverhalt {sachverhalt.id}: Entitäts-Register — " + "; ".join(reg_problems))
    rec = SachverhaltRecord(id=sachverhalt.id, sachverhalt=sachverhalt, source=source,
                            status=status)
    return sachverhalt_store.upsert(rec)


def seed_sachverhalte(sachverhalt_store=None, *, status: str = "in_review"):
    """Stage the curated Sachverhalte (library/sachverhalte.py) for review (cf. seed_texts)."""
    from ..library.sachverhalte import SACHVERHALTE
    from ..store.sachverhaltstore import SachverhaltStore

    store = sachverhalt_store or SachverhaltStore()
    return [ingest_sachverhalt(store, sv, status=status) for sv in SACHVERHALTE]


def compose_sachverhalt_worksheet(store: ReviewStore, sachverhalt_store, sach_id: str,
                                  *, klasse: int | None = None,
                                  today: date | None = None) -> ReviewItem:
    """Stage a worksheet derived from a Sachverhalt as a content item for Gate-2 review. The
    Darstellung is grounded prose; the Sachkompetenz answers are COMPUTED from the facts."""
    from ..pipeline.sachverhalt import build_worksheet

    rec = sachverhalt_store.get(sach_id)
    if rec is None:
        raise KeyError(f"no Sachverhalt '{sach_id}'")
    sv = rec.sachverhalt
    item = ReviewItem(
        id="", stage="content", source="sachverhalt",
        title=f"{sv.subject} {klasse or sv.default_klasse()}. Kl. — {sv.topic}",
        request=BundleRequest(subject=sv.subject, klasse=klasse or sv.default_klasse(),
                              topic_raw=sv.topic),
    )
    store.create(item)
    try:
        content, res = build_worksheet(sv, klasse=klasse, today=today)
        item.resolution = res
        assemble(content, res)
        report = verify(content, res)
        item.artifacts = _render_all(item.id, content)
        item.content = content
        item.verify_problems = report.problems
        item.verify_warnings = report.warnings
        item.status = "pending"
        item.error = None
    except Exception as exc:  # noqa: BLE001
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
def approve_content(store: ReviewStore, item_id: str, *, block_store=None) -> ReviewItem:
    item = store.get(item_id)
    if item is None or item.stage != "content":
        raise KeyError(f"no content item '{item_id}'")
    item.status = "approved"  # enters the representable-material library
    store.append_feedback(item_id, "approve")
    item = store.save(item)
    # Cascade (SME decision, 2 Jul 2026): reviewing the worksheet IS reviewing its
    # blocks — the harvested blocks enter the corpus with it. Undo = reject the
    # block individually in Prüfen/Bausteine.
    if block_store is not None:
        key = f"harvested:{item_id}"
        for lb in block_store.list():
            if lb.provenance == key and lb.status == "in_review":
                block_store.set_status(lb.id, "approved")
    return item


def reject(store: ReviewStore, item_id: str, note: str = "", *, block_store=None) -> ReviewItem:
    item = store.get(item_id)
    if item is None:
        raise KeyError(item_id)
    item.status = "rejected"
    store.append_feedback(item_id, "reject", note)
    item = store.save(item)
    # the cascade's mirror: a rejected sheet's harvested blocks don't enter the corpus
    if block_store is not None and item.stage == "content":
        key = f"harvested:{item_id}"
        for lb in block_store.list():
            if lb.provenance == key and lb.status == "in_review":
                block_store.set_status(lb.id, "rejected")
    return item


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
