"""Ingest adversarial triage verdicts (runs/triage/verdicts.json) into the feedback log.

The write-back half of `tools/triage_prompt.py`: a subagent judged the staged entries
(Didaktik · Register · Lösungs-Konsistenz) and wrote one verdict per entry. Each verdict
is validated against the CURRENT queue (kind/id must still be staged; rating 1–5;
attention hoch|mittel|niedrig — invalid ones are reported and skipped) and recorded as a
"triage"-tagged `FeedbackStore` entry: rating + reasons as the comment, `revise` for
attention "hoch". `pipeline/triage.py::attention` picks the verdicts up, so the Prüfen
queue re-ranks — NOTHING is approved or rejected; the SME remains the gate (invariants §7).

    python tools/ingest_triage.py --dry-run
    python tools/ingest_triage.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.store.arrangementstore import ArrangementStore
from teachersaid.store.assetstore import AssetStore
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.datasetstore import DatasetStore
from teachersaid.store.feedbackstore import FeedbackEntry, FeedbackStore
from teachersaid.store.repository import ReviewStore
from teachersaid.store.reviewqueue import queue
from teachersaid.store.sachverhaltstore import SachverhaltStore
from teachersaid.store.textstore import TextStore

ATTENTION_LEVELS = ("hoch", "mittel", "niedrig")


def _validate(v, known: dict) -> str | None:
    """One verdict's problem (for the skip report), or None if it is valid."""
    if not isinstance(v, dict):
        return f"kein Objekt: {v!r}"
    if (v.get("kind"), v.get("id")) not in known:
        return f"unbekannter Queue-Eintrag {v.get('kind')}/{v.get('id')}"
    if v.get("rating") not in (1, 2, 3, 4, 5):
        return f"{v['kind']}/{v['id']}: rating muss 1–5 sein (ist {v.get('rating')!r})"
    if v.get("attention") not in ATTENTION_LEVELS:
        return (f"{v['kind']}/{v['id']}: attention muss hoch|mittel|niedrig sein "
                f"(ist {v.get('attention')!r})")
    return None


def ingest(verdicts: list, entries: list[dict], feedback: FeedbackStore,
           *, dry_run: bool = False) -> tuple[int, int]:
    """Validate each verdict against the queue envelope and record the valid ones as
    "triage"-tagged feedback. Returns (n_valid, n_skipped); `dry_run` writes nothing."""
    known = {(e["kind"], e["id"]): e for e in entries}
    valid = skipped = 0
    for v in verdicts:
        problem = _validate(v, known)
        if problem:
            print(f"SKIP {problem}")
            skipped += 1
            continue
        entry = known[(v["kind"], v["id"])]
        comment = "Triage: " + "; ".join(v.get("reasons") or [])
        watch = (v.get("watch") or "").strip()
        if watch:
            comment += " — " + watch
        if not dry_run:
            feedback.add(FeedbackEntry(
                target_kind=v["kind"], target_id=v["id"],
                subject=entry.get("subject") or "", label=entry.get("title") or "",
                rating=v["rating"], comment=comment, tags=["triage"],
                revise=v["attention"] == "hoch"))
        print(f"OK   {v['kind']}/{v['id']}: rating={v['rating']} attention={v['attention']}")
        valid += 1
    return valid, skipped


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--file", default=str(RUNS_DIR / "triage" / "verdicts.json"))
    args = ap.parse_args()
    verdicts = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if not isinstance(verdicts, list):
        raise SystemExit(f"{args.file}: erwartet eine JSON-Liste von Verdikten")
    q = queue(items=ReviewStore(), blocks=BlockStore(), assets=AssetStore(),
              datasets=DatasetStore(), texts=TextStore(),
              sachverhalte=SachverhaltStore(), arrangements=ArrangementStore())
    valid, skipped = ingest(verdicts, q["entries"], FeedbackStore(), dry_run=args.dry_run)
    mode = " (dry-run, nichts geschrieben)" if args.dry_run else ""
    print(f"\n== {valid} Verdikte übernommen, {skipped} übersprungen{mode} ==")


if __name__ == "__main__":
    main()
