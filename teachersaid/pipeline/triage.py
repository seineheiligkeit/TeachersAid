"""Review triage — a deterministic attention score over the Prüfen queue (Track 1 #3c).

The queue tells the SME WHAT is staged; triage tells her where to look FIRST. Two
cleanly layered signal sources:

- `heuristic(entry)` — a deterministic 0–100 score computed from the queue envelope
  dict alone (verify findings, review tier, empty/incomplete items). No store reads,
  no LLM: the same envelope always scores the same.
- `attention(entry, feedback_store)` — the heuristic PLUS the latest "triage"-tagged
  feedback verdict for the entry, when a store is given: an adversarial reviewer's
  expected-quality rating bubbles weak items up and lets solid ones sink
  (`tools/triage_prompt.py` writes the judging brief, `tools/ingest_triage.py`
  records the verdicts as feedback entries).

Triage RANKS, it never decides: nothing is approved or rejected here — the SME
remains the gate (invariants §7). Scores only order the queue.
"""

from __future__ import annotations

# tier weight: how much honest reading the correctness mechanism leaves to the SME
# (the reviewqueue tiers — curated needs a full read, computed only a confirmation)
_TIER_WEIGHT = {"voll": 20, "sprache": 12, "quelle": 8, "bestaetigen": 0}
_TIER_REASON = {"voll": "Stufe: voll lesen", "sprache": "Stufe: Sprache lesen",
                "quelle": "Stufe: Quelle prüfen"}
_WARN_STEP, _WARN_CAP = 10, 40


def heuristic(entry: dict) -> tuple[int, list[str]]:
    """Deterministic attention score 0–100 + short German reasons, computed from the
    queue envelope dict alone (no store reads).

    Verify problems and warnings arrive merged in the envelope's `warnings`, so each
    counts +10 (capped at +40); the review tier adds its reading depth; an empty
    worksheet or missing metadata is suspicious by construction.
    """
    score = 0
    reasons: list[str] = []
    n_warn = entry.get("n_warnings") or 0
    if n_warn:
        score += min(_WARN_STEP * n_warn, _WARN_CAP)
        reasons.append(f"{n_warn} Prüf-Hinweis{'e' if n_warn != 1 else ''}")
    tier = entry.get("tier") or ""
    if _TIER_WEIGHT.get(tier, 0):
        score += _TIER_WEIGHT[tier]
        reasons.append(_TIER_REASON[tier])
    if entry.get("n_tasks") == 0:  # only worksheet items carry n_tasks
        score += 30
        reasons.append("keine Aufgaben")
    if not entry.get("subject") or not entry.get("klasse"):
        score += 10
        reasons.append("unvollständige Metadaten")
    return max(0, min(100, score)), reasons


def latest_triage(feedback_store) -> dict:
    """The newest "triage"-tagged feedback entry per (target_kind, target_id) — ONE
    store read, so scoring a whole queue never re-reads the log per entry. Ties on
    the second-resolution timestamp break by the sequential id (later id = later)."""
    idx: dict[tuple[str, str], object] = {}
    for e in sorted(feedback_store.list(), key=lambda e: (e.at, e.id)):
        if "triage" in e.tags:
            idx[(e.target_kind, e.target_id)] = e  # later write wins ⇒ the latest
    return idx


def attention(entry: dict, feedback_store=None, *, triage_index: dict | None = None) -> dict:
    """The heuristic combined with the latest triage verdict:
    `{"score": int, "reasons": [...], "rating": r | None}`.

    A stored triage rating r (1–5) shifts the score by (3−r)·10 — expected-weak items
    (r=1,2) bubble up, expected-solid ones (r=4,5) sink — and a `revise` flag adds
    +25. Pass `triage_index` (from `latest_triage`) when scoring many entries against
    one store; a bare `feedback_store` builds it per call.
    """
    score, reasons = heuristic(entry)
    if triage_index is None:
        triage_index = latest_triage(feedback_store) if feedback_store is not None else {}
    fb = triage_index.get((entry.get("kind", ""), entry.get("id", "")))
    rating = None
    if fb is not None:
        rating = fb.rating
        if rating is not None:
            score += (3 - rating) * 10
        if fb.revise:
            score += 25
            reasons.append("Triage: überarbeiten empfohlen")
    return {"score": max(0, min(100, score)), "reasons": reasons, "rating": rating}
