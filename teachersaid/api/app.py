"""FastAPI app: the brainstorm → content review pipeline + the single-page dashboard.

Stages: a `brainstorm` idea (rough, user- or AI-produced) is approved, then *fleshed
out* into a `content` item (the worksheet — structured blocks + rendered PDFs), which
is approved into the material library. Offline, generation is served from the master
library; the store is JSON-file-backed under RUNS_DIR/store.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from ..config import RUNS_DIR
from ..pipeline import orchestrator as orch
from ..pipeline.assets import build_asset
from ..stats import compute_stats
from ..store.arrangementstore import ArrangementStore
from ..store.assetstore import AssetStore
from ..store.blockstore import BlockStore
from ..store.datasetstore import DatasetStore
from ..store.textstore import TextStore
from ..store.sachverhaltstore import SachverhaltStore
from ..store.feedbackstore import FEEDBACK_TAGS, TARGET_KINDS, FeedbackEntry, FeedbackStore
from ..store.repository import ReviewStore

app = FastAPI(title="TeachersAid — Review Dashboard")
STORE = ReviewStore()
BLOCKS = BlockStore()
ASSETS = AssetStore()
ARRANGEMENTS = ArrangementStore()
DATASETS = DatasetStore()
TEXTS = TextStore()
SACHVERHALTE = SachverhaltStore()
FEEDBACK = FeedbackStore()
_STATIC = Path(__file__).resolve().parent / "static"


# --- request bodies ----------------------------------------------------------
class BrainstormBody(BaseModel):
    subject: str = "Physik"
    klasse: int = 4
    topic: str = ""
    note: str = ""


class SuggestBody(BaseModel):
    subject: str = "Physik"
    klasse: int = 4


class ComposeBody(BaseModel):
    subject: str = "Physik"
    klasse: int = 4
    topic: str = ""
    envelope: str = "doppelstunde"
    kompetenzbereich: str | None = None


class NoteBody(BaseModel):
    note: str = ""


class FeedbackBody(BaseModel):
    target_kind: str
    target_id: str
    rating: int | None = None
    comment: str = ""
    tags: list[str] = []
    revise: bool = False


# --- dashboard ---------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return (_STATIC / "index.html").read_text(encoding="utf-8")


# --- ideation ----------------------------------------------------------------
@app.post("/api/brainstorm")
def brainstorm(body: BrainstormBody):
    if not body.topic.strip():
        raise HTTPException(400, "topic required")
    return orch.submit_brainstorm(
        STORE, body.subject, body.klasse, body.topic.strip(), body.note.strip(),
        source="user",
    ).summary()


@app.post("/api/brainstorm/suggest")
def suggest(body: SuggestBody):
    items = orch.suggest_from_catalog(STORE, body.subject, body.klasse)
    return {"created": [i.summary() for i in items]}


@app.post("/api/compose")
def compose(body: ComposeBody):
    kb = (body.kompetenzbereich or "").strip() or None
    if not body.topic.strip() and not kb:
        raise HTTPException(400, "topic or kompetenzbereich required")
    return orch.compose_worksheet(
        STORE, BLOCKS, body.subject, body.klasse, body.topic.strip(), body.envelope,
        kompetenzbereich=kb,
    ).summary()


@app.get("/api/kompetenzbereiche")
def kompetenzbereiche(subject: str, klasse: int):
    """The Kompetenzbereiche of a subject+grade, for the compose form's target picker
    (verbatim catalog labels, so they match what blocks were tagged with)."""
    from ..grounding import lehrplan_store as ls
    return {"kompetenzbereiche": ls.grade_map(subject).get(klasse, [])}


# --- queues / stats ----------------------------------------------------------
@app.get("/api/status")
def status():
    return {
        "counts": STORE.status_counts(),
        "library_size": len(STORE.library()),
        "items": [i.summary() for i in STORE.list()],
    }


@app.get("/api/queue")
def queue(stage: str | None = None, status: str | None = None):
    return [i.summary() for i in STORE.list(stage=stage, status=status)]


@app.get("/api/library")
def library():
    return [i.summary() for i in STORE.library()]


@app.get("/api/stats")
def stats():
    return compute_stats(BLOCKS, STORE)


# --- human feedback (the HITL loop) ------------------------------------------
def _target_meta(kind: str, tid: str) -> tuple[str, str]:
    """(subject, label) for a feedback target — denormalised so the digest can group
    without re-reading every store."""
    if kind == "block":
        b = BLOCKS.get(tid)
        if b:
            return b.subject, f"{b.role}·{b.kind}: {b.summary().get('prompt', '')[:60]}"
    elif kind == "item":
        it = STORE.get(tid)
        if it:
            subj = it.content.meta.subject if it.content else it.request.subject
            return subj, it.title
    elif kind == "arrangement":
        r = ARRANGEMENTS.get(tid)
        if r:
            return r.arrangement.meta.subject, r.title
    elif kind == "asset":
        a = ASSETS.get(tid)
        if a:
            return "", f"{a.klass}·{a.asset.role}: {a.id}"
    elif kind == "dataset":
        rec = DATASETS.get(tid)
        if rec:
            return "", f"{rec.dataset.source.publisher}: {rec.dataset.title}"
    elif kind == "text":
        rec = TEXTS.get(tid)
        if rec:
            return rec.text.subject, f"{rec.text.source.author}: {rec.text.title}"
    elif kind == "sachverhalt":
        rec = SACHVERHALTE.get(tid)
        if rec:
            return rec.sachverhalt.subject, rec.sachverhalt.topic
    return "", tid


@app.post("/api/feedback")
def add_feedback(body: FeedbackBody):
    if body.target_kind not in TARGET_KINDS:
        raise HTTPException(400, f"target_kind must be one of {TARGET_KINDS}")
    if body.rating is not None and body.rating not in (1, 2, 3, 4, 5):
        raise HTTPException(400, "rating must be 1–5")
    subject, label = _target_meta(body.target_kind, body.target_id)
    entry = FEEDBACK.add(FeedbackEntry(
        target_kind=body.target_kind, target_id=body.target_id, subject=subject, label=label,
        rating=body.rating, comment=body.comment.strip(), tags=body.tags, revise=body.revise))
    # "revise with feedback": for a worksheet item, also kick the existing regenerate
    # path (feedback as the note). Other kinds carry the revise flag into the digest,
    # where the AI picks them up (they have no in-dashboard regenerate path).
    if body.revise and body.target_kind == "item" and STORE.get(body.target_id) is not None:
        note = body.comment.strip()
        if body.tags:
            note = (note + " [" + ", ".join(body.tags) + "]").strip()
        try:
            orch.request_changes(STORE, body.target_id, note or "Überarbeiten (Feedback)")
        except Exception:  # noqa: BLE001 — feedback is recorded regardless
            pass
    return entry.model_dump()


@app.get("/api/feedback")
def feedback_for(target_kind: str, target_id: str):
    return [e.model_dump() for e in FEEDBACK.for_target(target_kind, target_id)]


@app.get("/api/feedback/digest")
def feedback_digest():
    return FEEDBACK.digest()


@app.get("/api/feedback/tags")
def feedback_tags():
    return {"tags": list(FEEDBACK_TAGS)}


@app.get("/api/assets")
def assets_overview():
    """The asset-review gallery: every figure in the system, deduped by
    (generator, spec). Code-gen assets are specs that travel with blocks (3c), so
    this is a *view over* them — not a separate store. Each entry carries a preview
    URL (pointing at a block/item source) plus where it is used and its review state."""
    gallery: dict[str, dict] = {}

    def _entry(a, preview: str) -> dict:
        key = f"{a.generator}|{json.dumps(a.spec, sort_keys=True, ensure_ascii=False)}"
        return gallery.setdefault(key, {
            "generator": a.generator, "caption": a.caption, "spec": a.spec,
            "blocks": [], "items": [], "subjects": set(), "statuses": [],
            "preview": preview,
        })

    for lb in BLOCKS.list():
        for a in lb.assets:
            if not a.generator:
                continue
            e = _entry(a, f"/api/blocks/{lb.id}/asset/{a.id}")
            e["blocks"].append({"id": lb.id, "status": lb.status})
            e["subjects"].add(lb.subject)
            e["statuses"].append(lb.status)
    for it in STORE.list():
        if it.content is None:
            continue
        for a in it.content.assets:
            if not a.generator:
                continue
            e = _entry(a, f"/api/items/{it.id}/asset/{a.id}")
            e["items"].append({"id": it.id, "title": it.title})
            e["subjects"].add(it.content.meta.subject)

    out = []
    for e in gallery.values():
        e["subjects"] = sorted(e["subjects"])
        e["n_blocks"] = len(e["blocks"])
        e["n_items"] = len(e["items"])
        e["approved"] = sum(s == "approved" for s in e["statuses"])
        out.append(e)
    out.sort(key=lambda e: (e["generator"], -e["n_blocks"] - e["n_items"]))
    return out


# --- asset library (file-backed: decorative + sourced) -----------------------
@app.get("/api/asset-library")
def asset_library(klass: str | None = None, status: str | None = None):
    return [a.summary() for a in ASSETS.list(klass=klass, status=status)]


@app.get("/api/asset-library/{asset_id}/file")
def asset_library_file(asset_id: str):
    la = ASSETS.get(asset_id)
    if la is None or not la.file or not Path(la.file).exists():
        raise HTTPException(404, "no file for this asset")
    media = {
        ".png": "image/png", ".svg": "image/svg+xml", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
    }.get(Path(la.file).suffix.lower(), "application/octet-stream")
    return FileResponse(la.file, media_type=media)


@app.post("/api/asset-library/{asset_id}/approve")
def approve_asset(asset_id: str):
    if ASSETS.get(asset_id) is None:
        raise HTTPException(404, "no such asset")
    return ASSETS.set_status(asset_id, "approved").summary()


@app.post("/api/asset-library/{asset_id}/reject")
def reject_asset(asset_id: str):
    if ASSETS.get(asset_id) is None:
        raise HTTPException(404, "no such asset")
    return ASSETS.set_status(asset_id, "rejected").summary()


# --- grounded-facts dataset library ------------------------------------------
def _dataset_figure_asset(rec, series_key: str):
    """Build a preview Asset for one series of a dataset (pyramid or a bar of the
    series' values), so the reviewer sees the actual figure the data produces."""
    from ..schema.assets import Asset

    series = rec.dataset.series.get(series_key)
    if not series:
        return None
    title = f"{rec.dataset.title} — {series.get('label', series_key)}"
    if series.get("kind") == "population_pyramid":
        return Asset(id=f"{rec.id}__{series_key}", role="figure",
                     generator="matplotlib:population_pyramid",
                     spec={"age_groups": series.get("age_groups", []),
                           "male": series.get("male", []), "female": series.get("female", []),
                           "title": title})
    if "shares_pct" in series or "counts" in series:
        vals = series.get("shares_pct") or series.get("counts") or []
        return Asset(id=f"{rec.id}__{series_key}", role="figure",
                     generator="matplotlib:bar_chart",
                     spec={"categories": series.get("groups", []), "values": vals,
                           "ylabel": "Anteil (%)" if "shares_pct" in series else (rec.dataset.unit or ""),
                           "title": title})
    return None


@app.get("/api/datasets")
def datasets(status: str | None = None):
    return [r.summary() for r in DATASETS.list(status=status)]


@app.get("/api/datasets/{dataset_id}")
def dataset_detail(dataset_id: str):
    rec = DATASETS.get(dataset_id)
    if rec is None:
        raise HTTPException(404, "no such dataset")
    s = rec.summary()
    s["series_data"] = rec.dataset.series
    return s


@app.get("/api/datasets/{dataset_id}/figure")
def dataset_figure(dataset_id: str, series: str):
    rec = DATASETS.get(dataset_id)
    if rec is None:
        raise HTTPException(404, "no such dataset")
    asset = _dataset_figure_asset(rec, series)
    if asset is None:
        raise HTTPException(404, "no figure for this series")
    out = RUNS_DIR / "datasets_fig"
    path = build_asset(asset, outdir=out)
    return FileResponse(path, media_type="image/png")


@app.post("/api/datasets/{dataset_id}/approve")
def approve_dataset(dataset_id: str):
    if DATASETS.get(dataset_id) is None:
        raise HTTPException(404, "no such dataset")
    return DATASETS.set_status(dataset_id, "approved").summary()


@app.post("/api/datasets/{dataset_id}/reject")
def reject_dataset(dataset_id: str):
    if DATASETS.get(dataset_id) is None:
        raise HTTPException(404, "no such dataset")
    return DATASETS.set_status(dataset_id, "rejected").summary()


# --- annotated authentic texts (Deutsch) -------------------------------------
@app.get("/api/texts")
def texts(status: str | None = None):
    return [r.summary() for r in TEXTS.list(status=status)]


@app.get("/api/texts/{text_id}")
def text_detail(text_id: str):
    rec = TEXTS.get(text_id)
    if rec is None:
        raise HTTPException(404, "no such text")
    s = rec.summary()
    s["text"] = rec.text.text
    s["annotations"] = [a.model_dump() for a in rec.text.annotations]
    return s


@app.post("/api/texts/{text_id}/approve")
def approve_text(text_id: str):
    if TEXTS.get(text_id) is None:
        raise HTTPException(404, "no such text")
    return TEXTS.set_status(text_id, "approved").summary()


@app.post("/api/texts/{text_id}/reject")
def reject_text(text_id: str):
    if TEXTS.get(text_id) is None:
        raise HTTPException(404, "no such text")
    return TEXTS.set_status(text_id, "rejected").summary()


@app.post("/api/texts/{text_id}/compose")
def compose_text(text_id: str):
    """Derive a worksheet from the annotated text and stage it in Inhalte for review."""
    if TEXTS.get(text_id) is None:
        raise HTTPException(404, "no such text")
    item = orch.compose_text_worksheet(STORE, TEXTS, text_id)
    return {"id": item.id, "error": item.error, "problems": item.verify_problems}


# --- Sachverhalte (the content / exposition layer) ---------------------------
def _sv_plain(rt) -> str:
    from ..schema.richtext import plain_text
    return plain_text(rt) if rt else ""


@app.get("/api/sachverhalte")
def sachverhalte(status: str | None = None):
    return [r.summary() for r in SACHVERHALTE.list(status=status)]


@app.get("/api/sachverhalte/{sach_id}")
def sachverhalt_detail(sach_id: str):
    rec = SACHVERHALTE.get(sach_id)
    if rec is None:
        raise HTTPException(404, "no such Sachverhalt")
    s = rec.summary()
    sv = rec.sachverhalt
    s["timeline"] = [{"at": e.at, "label": e.label} for e in sv.timeline]
    s["actors"] = [{"name": a.name, "role": _sv_plain(a.role)} for a in sv.actors]
    s["causes"] = [{"cause": c.cause, "effect": c.effect, "kind": c.kind} for c in sv.causes]
    s["concepts"] = [{"term": c.term, "definition": _sv_plain(c.definition)}
                     for c in sv.concepts]
    s["darstellung"] = [{"heading": d.heading, "body": _sv_plain(d.body)}
                        for d in sv.darstellung]
    s["bedeutung"] = _sv_plain(sv.bedeutung)
    s["gegenwartsbezug"] = _sv_plain(sv.gegenwartsbezug)
    s["facts_sources"] = [{"title": q.title, "publisher": q.publisher, "url": q.url,
                           "licence": q.licence, "role": q.role} for q in sv.sources]
    return s


@app.post("/api/sachverhalte/{sach_id}/approve")
def approve_sachverhalt(sach_id: str):
    if SACHVERHALTE.get(sach_id) is None:
        raise HTTPException(404, "no such Sachverhalt")
    return SACHVERHALTE.set_status(sach_id, "approved").summary()


@app.post("/api/sachverhalte/{sach_id}/reject")
def reject_sachverhalt(sach_id: str):
    if SACHVERHALTE.get(sach_id) is None:
        raise HTTPException(404, "no such Sachverhalt")
    return SACHVERHALTE.set_status(sach_id, "rejected").summary()


@app.post("/api/sachverhalte/{sach_id}/compose")
def compose_sachverhalt(sach_id: str):
    """Derive a worksheet from the Sachverhalt and stage it in Inhalte for review."""
    if SACHVERHALTE.get(sach_id) is None:
        raise HTTPException(404, "no such Sachverhalt")
    item = orch.compose_sachverhalt_worksheet(STORE, SACHVERHALTE, sach_id)
    return {"id": item.id, "error": item.error, "problems": item.verify_problems}


# --- Lernarrangements (v0.5) -------------------------------------------------
@app.get("/api/arrangements")
def arrangements(status: str | None = None):
    return [r.summary() for r in ARRANGEMENTS.list(status=status)]


@app.get("/api/arrangements/{arr_id}")
def get_arrangement(arr_id: str):
    rec = ARRANGEMENTS.get(arr_id)
    if rec is None:
        raise HTTPException(404, "no such arrangement")
    return rec.model_dump()


def _arr_pdf(arr_id: str, path: str | None) -> FileResponse:
    if not path or not Path(path).exists():
        raise HTTPException(404, "no such PDF")
    return FileResponse(path, media_type="application/pdf")


@app.get("/api/arrangements/{arr_id}/pdf/orchestration")
def arrangement_orchestration(arr_id: str):
    rec = ARRANGEMENTS.get(arr_id)
    if rec is None or rec.artifacts is None:
        raise HTTPException(404, "no such arrangement")
    return _arr_pdf(arr_id, rec.artifacts.orchestration)


@app.get("/api/arrangements/{arr_id}/pdf/{role_id}/{which}")
def arrangement_role_pdf(arr_id: str, role_id: str, which: str):
    rec = ARRANGEMENTS.get(arr_id)
    if rec is None or rec.artifacts is None:
        raise HTTPException(404, "no such arrangement")
    role = next((r for r in rec.artifacts.roles if r.get("id") == role_id), None)
    if role is None or which not in ("student", "teacher"):
        raise HTTPException(404, "no such role PDF")
    return _arr_pdf(arr_id, role.get(which))


@app.post("/api/arrangements/{arr_id}/approve")
def approve_arrangement(arr_id: str):
    if ARRANGEMENTS.get(arr_id) is None:
        raise HTTPException(404, "no such arrangement")
    return ARRANGEMENTS.set_status(arr_id, "approved").summary()


@app.post("/api/arrangements/{arr_id}/reject")
def reject_arrangement(arr_id: str):
    if ARRANGEMENTS.get(arr_id) is None:
        raise HTTPException(404, "no such arrangement")
    return ARRANGEMENTS.set_status(arr_id, "rejected").summary()


# --- block library -----------------------------------------------------------
@app.get("/api/blocks")
def blocks(subject: str | None = None, status: str | None = None, role: str | None = None):
    return [b.summary() for b in BLOCKS.list(subject=subject, status=status, role=role)]


@app.post("/api/blocks/approve-all")
def approve_all_blocks():
    n = 0
    for b in BLOCKS.list(status="in_review"):
        BLOCKS.set_status(b.id, "approved")
        n += 1
    return {"approved": n}


@app.get("/api/blocks/{block_id}")
def get_block(block_id: str):
    lb = BLOCKS.get(block_id)
    if lb is None:
        raise HTTPException(404, "no such block")
    return lb.model_dump()


@app.post("/api/blocks/{block_id}/approve")
def approve_block(block_id: str):
    if BLOCKS.get(block_id) is None:
        raise HTTPException(404, "no such block")
    return BLOCKS.set_status(block_id, "approved").summary()


@app.post("/api/blocks/{block_id}/reject")
def reject_block(block_id: str):
    if BLOCKS.get(block_id) is None:
        raise HTTPException(404, "no such block")
    return BLOCKS.set_status(block_id, "rejected").summary()


def _safe(s: str) -> str:
    return s.replace("/", "__").replace("\\", "__")


def _serve_asset(asset, outdir: Path) -> FileResponse:
    """Build (and cache) a code-generated asset's PNG on demand, then serve it.
    The spec is the source of truth (correct-by-construction); the PNG is a cache."""
    png = outdir / f"{asset.id}.png"
    if not png.exists():
        try:
            build_asset(asset, outdir=outdir)
        except Exception as e:  # noqa: BLE001 — surface the build failure to the reviewer
            raise HTTPException(422, f"asset build failed: {e}")
    return FileResponse(png, media_type="image/png")


@app.get("/api/blocks/{block_id}/asset/{asset_id}")
def block_asset(block_id: str, asset_id: str):
    """Render a library block's figure for inline review (Bausteine). The asset spec
    travels with the block (3c), so this is built straight from it — no worksheet."""
    lb = BLOCKS.get(block_id)
    if lb is None:
        raise HTTPException(404, "no such block")
    asset = next((a for a in lb.assets if a.id == asset_id), None)
    if asset is None or not asset.generator:
        raise HTTPException(404, "no such asset")
    return _serve_asset(asset, RUNS_DIR / "_preview" / "blocks" / _safe(block_id))


# --- item detail + review ----------------------------------------------------
@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    return item.model_dump()  # full content (blocks) included for the Blöcke view


@app.post("/api/items/{item_id}/flesh-out")
def flesh_out(item_id: str):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    if item.stage != "brainstorm":
        raise HTTPException(400, "only brainstorm ideas can be fleshed out")
    return orch.flesh_out(STORE, item_id).summary()


@app.post("/api/items/{item_id}/approve")
def approve(item_id: str):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    if item.stage == "brainstorm":
        return orch.approve_brainstorm(STORE, item_id).summary()
    return orch.approve_content(STORE, item_id).summary()


@app.post("/api/items/{item_id}/reject")
def reject(item_id: str, body: NoteBody):
    if STORE.get(item_id) is None:
        raise HTTPException(404, "no such item")
    return orch.reject(STORE, item_id, body.note).summary()


@app.post("/api/items/{item_id}/request-changes")
def request_changes(item_id: str, body: NoteBody):
    if STORE.get(item_id) is None:
        raise HTTPException(404, "no such item")
    return orch.request_changes(STORE, item_id, body.note).summary()


# --- artifacts ---------------------------------------------------------------
def _artifact_path(item_id: str, kind: str) -> Path:
    item = STORE.get(item_id)
    if item is None or item.artifacts is None:
        raise HTTPException(404, "no artifacts")
    mapping = {
        "student": item.artifacts.student_pdf,
        "teacher": item.artifacts.teacher_pdf,
        "homework": item.artifacts.homework_pdf,
        "preview": item.artifacts.preview_png,
    }
    p = mapping.get(kind)
    if not p or not Path(p).exists():
        raise HTTPException(404, f"no {kind} artifact")
    return Path(p)


@app.get("/api/items/{item_id}/pdf/{kind}")
def get_pdf(item_id: str, kind: str):
    p = _artifact_path(item_id, kind)
    media = "image/png" if kind == "preview" else "application/pdf"
    return FileResponse(p, media_type=media)


@app.get("/api/items/{item_id}/asset/{asset_id}")
def item_asset(item_id: str, asset_id: str):
    """Serve a worksheet's figure for the structured Blöcke view (rendered items
    already have it on disk; build on demand otherwise)."""
    item = STORE.get(item_id)
    if item is None or item.content is None:
        raise HTTPException(404, "no such item")
    asset = next((a for a in item.content.assets if a.id == asset_id), None)
    if asset is None or not asset.generator:
        raise HTTPException(404, "no such asset")
    return _serve_asset(asset, RUNS_DIR / "store" / item_id / "assets")
