"""Ingest subagent-annotated texts (runs/ingest/texts/<id>.json) through the real seam.

The annotation analogue of `tools/ingest_batch.py`: each file is an `AnnotatedText` JSON
(a REAL public-domain text + a curated annotation layer). `--dry-run` validates (schema →
rights gate → build_worksheet → assemble → verify) and reports; without it, clean texts
are staged into the TextStore for HITL review. The text itself is *selected* (verbatim,
cited), never authored — the subagent only adds the annotation layer.

    python tools/ingest_texts.py --dry-run
    python tools/ingest_texts.py
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.text_tasks import build_worksheet
from teachersaid.pipeline.verify import verify
from teachersaid.schema.texts import AnnotatedText
from teachersaid.store.textstore import TextStore

GEN_DATE = date(2026, 3, 1)

# the recurring agent JSON slip: „…" opened typographic, closed with a straight " (breaks
# the JSON string). Convert only that closing " to the typographic “ (cf. ingest_batch).
_GERMAN_QUOTE_FIX = re.compile(r'„([^"„“”]*)(?<!\\)"')


def _repair_text(raw: str) -> str:
    return _GERMAN_QUOTE_FIX.sub(r'„\1“', raw)


def _load(path: Path) -> AnnotatedText:
    raw = _repair_text(path.read_text(encoding="utf-8"))
    return AnnotatedText.model_validate(json.loads(raw, strict=False))


def dry_run(paths: list[Path]) -> None:
    ok = bad = 0
    for p in paths:
        try:
            at = _load(p)
        except Exception as e:  # noqa: BLE001
            print(f"!! {p.stem}: SCHEMA/JSON ERROR: {str(e)[:200]}"); bad += 1; continue
        rights_ok, reasons = at.source.is_clear(GEN_DATE.year)
        content, res = build_worksheet(at, today=GEN_DATE)
        assemble(content, res)
        rep = verify(content, res)
        clean = rights_ok and not rep.problems
        nt = sum(1 for b in content.iter_blocks() if b.role == "task")
        print(f"{'OK ' if clean else '!! '}{at.id}: '{at.title[:40]}' kl{at.klasse} "
              f"rights={rights_ok} annos={len(at.annotations)} tasks={nt} problems={len(rep.problems)}")
        for r in reasons:
            print("      rights:", r)
        for x in rep.problems:
            print("      problem:", x)
        ok += clean
        bad += not clean
    print(f"\n== {ok} clean, {bad} need attention, {len(paths)} total ==")


def persist(paths: list[Path]) -> None:
    store = TextStore()
    for p in paths:
        at = _load(p)
        rec = orch.ingest_text(store, at, today=GEN_DATE)
        print(f"{at.id}: {rec.status} ({len(at.annotations)} annotations)")
    print(f"\n== staged {len(paths)} annotated text(s) ==")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dir", default=str(RUNS_DIR / "ingest" / "texts"))
    args = ap.parse_args()
    paths = sorted(Path(args.dir).glob("*.json"))
    (dry_run if args.dry_run else persist)(paths)
