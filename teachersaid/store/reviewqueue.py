"""The unified review queue (Prüfen) — a READ-MODEL over the seven review stores.

One envelope per staged item, whatever its kind, with a review TIER derived from
the item's correct-by-construction mechanism (invariants §3): computed →
"bestaetigen", selected → "quelle", re-expressed-under-constraint → "sprache",
curated → "voll". The tier decides how much SME attention an item needs — the
lanes of the Prüfen tab; "bestaetigen" is safely bulk-releasable, "voll" is the
honest full read. Stores stay untouched (§9): this module aggregates and
classifies, it owns no state; decisions dispatch to each store's own lifecycle
(the worksheet→blocks approval cascade lives in `orchestrator.approve_content`).
The classifier is a deterministic heuristic — when in doubt it grades DOWN to a
deeper tier, never up.
"""

from __future__ import annotations

from ..pipeline.triage import attention, latest_triage
from ..schema.enums import Role

TIERS = ("bestaetigen", "quelle", "sprache", "voll")
TIER_LABEL = {
    "bestaetigen": "Nur bestätigen — berechnet",
    "quelle": "Quelle prüfen — ausgewählt",
    "sprache": "Sprache lesen — re-expressed",
    "voll": "Voll lesen — kuratiert",
}


def tier_for_content(content) -> str:
    """Worksheet tier from its dominant correctness mechanism."""
    if content is None:
        return "voll"
    tasks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    if tasks and all(getattr(b, "solution_steps", None) for b in tasks):
        return "bestaetigen"          # computed: parametric/chemistry variants
    if any(getattr(a, "data_source", None) is not None
           for a in getattr(content, "assets", [])):
        return "quelle"               # selected: cited data figures (+ numbers lint)
    if any(getattr(b, "provenance", None) is not None for b in content.iter_blocks()):
        return "sprache"              # re-expressed: provenance-grounded prose
    return "voll"


def tier_for_block(lb) -> str:
    if getattr(lb.block, "solution_steps", None):
        return "bestaetigen"
    if any(getattr(a, "data_source", None) is not None for a in (lb.assets or [])):
        return "quelle"
    if getattr(lb.block, "provenance", None) is not None:
        return "sprache"
    return "voll"


def _entry(kind, rec_id, title, subject, klasse, status, tier,
           updated_at="", warnings=None, **extra) -> dict:
    e = {"kind": kind, "id": rec_id, "title": title or rec_id, "subject": subject,
         "klasse": klasse, "status": status, "tier": tier, "updated_at": updated_at,
         "warnings": (warnings or [])[:4], "n_warnings": len(warnings or [])}
    e.update(extra)
    return e


def _file_backed(store, kind, tier_fn) -> list[dict]:
    out = []
    for rec in store.list():
        if getattr(rec, "status", "") != "in_review":
            continue
        s = rec.summary() if hasattr(rec, "summary") else {}
        out.append(_entry(
            kind, rec.id,
            s.get("title") or s.get("label") or s.get("prompt") or rec.id,
            s.get("subject"), s.get("klasse"), rec.status,
            tier_fn(rec), getattr(rec, "updated_at", "")))
    return out


def queue(*, items, blocks, assets, datasets, texts, sachverhalte, arrangements,
          feedback=None) -> dict:
    """The Prüfen envelope: every staged item across all kinds + lane counts. Each
    entry carries its triage attention score (`pipeline/triage.py`) — feedback-informed
    when a `FeedbackStore` is given — and the queue is ordered by it."""
    entries: list[dict] = []

    for it in items.list(stage="content"):
        if it.status not in ("pending", "changes_requested"):
            continue
        entries.append(_entry(
            "item", it.id, it.title or it.request.topic_raw,
            it.request.subject, it.request.klasse, it.status,
            tier_for_content(it.content), it.updated_at,
            (it.verify_problems or []) + (it.verify_warnings or []),
            n_tasks=it.n_tasks()))

    for lb in blocks.list():
        if lb.status != "in_review":
            continue
        s = lb.summary()
        entries.append(_entry(
            "block", lb.id, s.get("prompt") or f"{lb.role}·{lb.kind}",
            lb.subject, lb.klasse, lb.status, tier_for_block(lb), lb.updated_at,
            role=lb.role, block_kind=lb.kind))

    def _text_tier(rec):
        at = getattr(rec, "text", None)
        return "sprache" if getattr(at, "origin", None) == "constructed" else "voll"

    entries += _file_backed(
        assets, "asset",
        lambda r: "bestaetigen" if getattr(r, "klass", "") == "decorative" else "quelle")
    entries += _file_backed(datasets, "dataset", lambda r: "quelle")
    entries += _file_backed(texts, "text", _text_tier)
    entries += _file_backed(sachverhalte, "sachverhalt", lambda r: "sprache")
    entries += _file_backed(arrangements, "arrangement", lambda r: "voll")

    # attention-first: triage score on top (findings, tier depth, triage verdicts),
    # ties broken newest-first (stable two-pass sort)
    idx = latest_triage(feedback) if feedback is not None else {}
    for e in entries:
        e["triage"] = attention(e, triage_index=idx)
    entries.sort(key=lambda e: e["updated_at"], reverse=True)
    entries.sort(key=lambda e: -e["triage"]["score"])

    lanes = {t: 0 for t in TIERS}
    for e in entries:
        lanes[e["tier"]] = lanes.get(e["tier"], 0) + 1
    return {"entries": entries, "lanes": lanes, "tier_labels": TIER_LABEL,
            "total": len(entries)}
