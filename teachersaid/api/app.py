"""FastAPI app: pipeline + review endpoints, and the single-page dashboard.

Generation runs in a BackgroundTask so the UI stays responsive (and GET /status
reflects in-flight work). The store is JSON-file-backed under RUNS_DIR/store.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from ..pipeline import orchestrator as orch
from ..schema.worksheet import BundleRequest
from ..store.repository import ReviewStore

app = FastAPI(title="TeachersAid — Review Dashboard")
STORE = ReviewStore()
_STATIC = Path(__file__).resolve().parent / "static"


# --- request bodies ----------------------------------------------------------
class GenerateBody(BaseModel):
    subject: str = "Physik"
    klasse: int = 4
    topic: str = "Strahlung und Radioaktivität"
    envelope: str = "doppelstunde"


class BatchBody(BaseModel):
    subject: str = "Physik"
    klasse: int = 4


class NoteBody(BaseModel):
    note: str = ""


# --- dashboard ---------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return (_STATIC / "index.html").read_text(encoding="utf-8")


# --- pipeline ----------------------------------------------------------------
@app.post("/api/generate")
def generate(body: GenerateBody):
    req = BundleRequest(
        subject=body.subject, klasse=body.klasse,
        topic_raw=body.topic, envelope=body.envelope,
    )
    item = orch.submit_on_demand(STORE, req)
    return item.summary()


@app.post("/api/batch")
def batch(body: BatchBody):
    items = orch.submit_batch(STORE, body.subject, body.klasse)
    return {"created": [i.summary() for i in items]}


@app.get("/api/status")
def status():
    items = STORE.list()
    return {
        "counts": STORE.status_counts(),
        "library_size": len(STORE.library()),
        "items": [i.summary() for i in items],
    }


@app.get("/api/queue")
def queue(stage: str | None = None, status: str | None = None):
    return [i.summary() for i in STORE.list(stage=stage, status=status)]


@app.get("/api/library")
def library():
    return [i.summary() for i in STORE.library()]


# --- review ------------------------------------------------------------------
@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    d = item.model_dump()
    # trim the heavy content body for the detail view; keep derived summaries.
    if item.content is not None:
        d["content"] = {
            "meta": item.content.meta.model_dump(),
            "nachweis": item.content.nachweis.model_dump() if item.content.nachweis else None,
            "depth_profile": item.content.depth_profile.model_dump() if item.content.depth_profile else None,
            "n_blocks": sum(1 for _ in item.content.iter_blocks()),
        }
    return d


@app.post("/api/items/{item_id}/approve")
def approve(item_id: str, background: BackgroundTasks):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    if item.stage == "idea":
        placeholder = orch.begin_idea_approval(STORE, item_id)
        background.add_task(orch.fill_content_item, STORE, placeholder.id)
        return {"approved_idea": item_id, "content_item": placeholder.summary()}
    return orch.approve_content(STORE, item_id).summary()


@app.post("/api/items/{item_id}/reject")
def reject(item_id: str, body: NoteBody):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    return orch.reject(STORE, item_id, body.note).summary()


@app.post("/api/items/{item_id}/request-changes")
def request_changes(item_id: str, body: NoteBody, background: BackgroundTasks):
    item = STORE.get(item_id)
    if item is None:
        raise HTTPException(404, "no such item")
    if item.stage == "content":
        STORE.append_feedback(item_id, "request-changes", body.note)
        refreshed = STORE.get(item_id)
        refreshed.status = "generating"
        STORE.save(refreshed)
        background.add_task(orch.fill_content_item, STORE, item_id)
        return refreshed.summary()
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
