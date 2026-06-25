"""FastAPI app: the brainstorm → content review pipeline + the single-page dashboard.

Stages: a `brainstorm` idea (rough, user- or AI-produced) is approved, then *fleshed
out* into a `content` item (the worksheet — structured blocks + rendered PDFs), which
is approved into the material library. Offline, generation is served from the master
library; the store is JSON-file-backed under RUNS_DIR/store.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from ..pipeline import orchestrator as orch
from ..stats import compute_stats
from ..store.blockstore import BlockStore
from ..store.repository import ReviewStore

app = FastAPI(title="TeachersAid — Review Dashboard")
STORE = ReviewStore()
BLOCKS = BlockStore()
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


class NoteBody(BaseModel):
    note: str = ""


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


# --- block library -----------------------------------------------------------
@app.get("/api/blocks")
def blocks(subject: str | None = None, status: str | None = None, role: str | None = None):
    return [b.summary() for b in BLOCKS.list(subject=subject, status=status, role=role)]


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
