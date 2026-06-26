"""Ingest generated Lernarrangement bodies through the real seam (v0.5 analogue of
`ingest_batch.py`).

`--dry-run` validates each (up-convert → assemble_arrangement → verify_arrangement)
WITHOUT persisting and prints a per-file report; without it, the clean bodies are
staged into the arrangement store for HITL review. Reuses `ingest_batch`'s first-pass
normalizer (the load-bearing slip-absorber) on each role's worksheet `material`.

    python tools/ingest_arrangements.py --dry-run
    python tools/ingest_arrangements.py            # stage into runs/arrangements
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline import arrange
from teachersaid.pipeline.arrange import assemble_arrangement, verify_arrangement
from teachersaid.pipeline.resolve import resolve_grade
from teachersaid.schema.arrangement import ArrangementMeta
from teachersaid.schema.generation_views import (
    GenArrangementBody,
    arrangement_body_to_canonical,
)
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.store.arrangementstore import ArrangementStore

# reuse the proven worksheet normalizer + quote repair (tools/ is sys.path[0] as a script)
from ingest_batch import _normalize, _repair_text  # type: ignore

GEN_DATE = date(2026, 3, 1)
_INFO_KEYS = {"role", "id", "kind", "content", "callout_role", "teacher_note",
              "watch_outs", "optional", "modality", "asset_refs", "flags"}


def _norm_info(b: dict) -> None:
    b["role"] = "info"
    if b.get("kind") not in {"prose", "key_fact", "example", "procedure", "figure",
                             "data_reference", "callout"}:
        b["kind"] = "prose"
    for k in [k for k in b if k not in _INFO_KEYS]:
        b.pop(k, None)


def _normalize_arr(body: dict) -> dict:
    for b in body.get("common_material", []):
        _norm_info(b)
    for b in body.get("debrief", []):
        _norm_info(b)
    for role in body.get("roles", []):
        mat = role.get("material")
        if isinstance(mat, dict):
            _normalize(mat)            # normalizes the role worksheet's intro+sections blocks
    return body


def _load(path: Path) -> dict:
    w = json.loads(_repair_text(path.read_text(encoding="utf-8")), strict=False)
    w["body"] = _normalize_arr(w["body"])
    return w


def _canonical(w: dict):
    model = ls.get_subject_model(w["subject"])
    meta = ArrangementMeta(
        title=w["title"], subject=w["subject"], stufe="Unterstufe", klasse=w["klasse"],
        kernfrage=w.get("kernfrage"), fassung=ls.get_fassung(), format=w["format"],
        lehrplan_label=f"{w['subject']} · {w['klasse']}. Kl.",
    )
    gb = GenArrangementBody.model_validate(w["body"])
    return arrangement_body_to_canonical(gb, meta=meta, subject_model=model)


def dry_run(paths: list[Path]) -> None:
    ok = bad = 0
    for path in paths:
        name = path.stem
        try:
            w = _load(path)
        except Exception as e:  # noqa: BLE001
            print(f"!! {name}: JSON LOAD ERROR: {str(e)[:200]}"); bad += 1; continue
        try:
            arr = _canonical(w)
            res = resolve_grade(w["subject"], w["klasse"], today=GEN_DATE)
            assemble_arrangement(arr, res)
            rep = verify_arrangement(arr, res)
        except Exception as e:  # noqa: BLE001
            print(f"!! {name}: BUILD/VERIFY RAISED: {type(e).__name__}: {str(e)[:240]}"); bad += 1; continue
        cov = arr.nachweis.competence_coverage
        anchor_only = sum(1 for c in cov if c.covered
                          and all(e.startswith("anchor:") for e in c.exercised_by))
        flag = "OK " if not rep.problems else "!! "
        print(f"{flag}{name}: '{w['title'][:42]}' kl{w['klasse']} {w['format']} "
              f"roles={len(arr.roles)} anchors={len(arr.competence_anchors)} "
              f"(anchor-only={anchor_only}) covered={sum(c.covered for c in cov)}/{len(cov)} "
              f"problems={len(rep.problems)}")
        for p in rep.problems:
            print("      PROBLEM:", p)
        ok += not rep.problems
        bad += bool(rep.problems)
    print(f"\n== {ok} clean, {bad} need attention, {len(paths)} total ==")


def persist(paths: list[Path]) -> None:
    store = ArrangementStore()
    for path in paths:
        w = _load(path)
        rec = arrange.ingest_arrangement(
            store, w["subject"], w["klasse"], title=w["title"], kernfrage=w.get("kernfrage", ""),
            format=w["format"], body=w["body"], arr_id=path.stem, source="generated", today=GEN_DATE)
        print(f"{path.stem}: id={rec.id} status={rec.status} roles={len(rec.arrangement.roles)} "
              f"problems={len(rec.verify_problems)}")
    print(f"\n== staged {len(paths)} arrangement(s) into the store ==")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dir", default=str(RUNS_DIR / "ingest" / "gen_arr"))
    args = ap.parse_args()
    paths = sorted(Path(args.dir).glob("*.json"))
    (dry_run if args.dry_run else persist)(paths)
