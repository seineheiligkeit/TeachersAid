"""Ingest generated worksheet bodies (runs/ingest/<CODE>.json) through the real seam.

`--dry-run` validates each body (resolve → to_canonical → assemble → verify) WITHOUT
persisting and prints a per-subject report — the first-pass diagnostic. Without it, the
clean bodies are staged as pending content items + harvested blocks for HITL review.

    python tools/ingest_batch.py --dry-run
    python tools/ingest_batch.py              # persist into runs/store + runs/blocks
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from teachersaid.config import RUNS_DIR
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.resolve import resolve_grade, resolve_kompetenzbereich
from teachersaid.pipeline.verify import verify
from teachersaid.schema.generation_views import GenWorksheetBody, body_to_canonical
from teachersaid.schema.worksheet import WorksheetMeta
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.repository import ReviewStore

GEN_DATE = date(2026, 3, 1)  # inside the Fassung window; deterministic
# common agent key-slips -> schema keys (first-pass normalization)
_RUBRIC_KEYMAP = {"kriterium": "criterion", "kriterien": "criterion", "stufen": "levels"}
_VALID_RELATIONS = {"exercises", "builds_prerequisite"}


def _stringify_level(lv):
    """A rubric level is a string; some agents emit {label, description}."""
    if isinstance(lv, str):
        return lv
    if isinstance(lv, dict):
        label = lv.get("label") or lv.get("stufe") or ""
        desc = lv.get("description") or lv.get("descriptor") or lv.get("beschreibung") or ""
        joined = f"{label}: {desc}".strip(": ").strip()
        return joined or " / ".join(str(v) for v in lv.values())
    return str(lv)


def _normalize(body: dict) -> dict:
    """Coerce common agent slips to the schema: German rubric keys, rich level objects,
    and non-standard `serves.relation` values (only exercises/builds_prerequisite are valid)."""
    for sec in body.get("sections", []):
        for b in sec.get("blocks", []):
            for s in b.get("serves", []):
                if s.get("relation") not in _VALID_RELATIONS:
                    s["relation"] = "exercises"
            rub = b.get("rubric")
            if isinstance(rub, list):
                fixed = []
                for r in rub:
                    r = {_RUBRIC_KEYMAP.get(k, k): v for k, v in r.items()}
                    if isinstance(r.get("levels"), list):
                        r["levels"] = [_stringify_level(lv) for lv in r["levels"]]
                    fixed.append(r)
                b["rubric"] = fixed
    return body


def _load(code: str) -> dict:
    w = json.loads((RUNS_DIR / "ingest" / f"{code}.json").read_text(encoding="utf-8"))
    w["body"] = _normalize(w["body"])
    return w


def _resolution(w: dict):
    subj, kl = w["subject"], w["klasse"]
    kb = w.get("kompetenzbereich")
    if kb:
        return resolve_kompetenzbereich(subj, kl, kb, today=GEN_DATE)
    return resolve_grade(subj, kl, today=GEN_DATE)


def dry_run(codes: list[str]) -> None:
    for code in codes:
        w = _load(code)
        res = _resolution(w)
        model = ls.get_subject_model(w["subject"])
        try:
            gb = GenWorksheetBody.model_validate(w["body"])
        except Exception as e:  # noqa: BLE001
            print(f"{code}: SCHEMA ERROR: {str(e)[:400]}"); continue
        meta = WorksheetMeta(
            title=w["title"], subject=w["subject"], stufe="Unterstufe", klasse=w["klasse"],
            kernfrage=w["kernfrage"], fassung=res.fassung,
            lehrplan_label=f"{w['subject']} · {w['klasse']}. Kl. · "
                           f"{w.get('kompetenzbereich') or w.get('scope_label')}",
        )
        content = body_to_canonical(gb, meta=meta, subject_model=model)
        try:
            assemble(content, res)
            rep = verify(content, res)
        except Exception as e:  # noqa: BLE001
            print(f"{code}: ASSEMBLE/VERIFY RAISED: {type(e).__name__}: {str(e)[:300]}"); continue
        nt = sum(1 for b in content.iter_blocks() if b.role == "task")
        cov = content.nachweis.competence_coverage
        print(f"{code}: '{w['title']}'  tasks={nt}  problems={len(rep.problems)}  "
              f"warnings={len(rep.warnings)}  coverage={sum(c.covered for c in cov)}/{len(cov)}")
        for p in rep.problems:
            print("    PROBLEM:", p)
        for wn in rep.warnings:
            print("    warn:", wn)


def persist(codes: list[str]) -> None:
    store, blocks = ReviewStore(), BlockStore()
    for code in codes:
        w = _load(code)
        item, n = orch.ingest_generated(
            store, blocks, w["subject"], w["klasse"],
            kompetenzbereich=w.get("kompetenzbereich"), scope_label=w.get("scope_label"),
            title=w["title"], kernfrage=w["kernfrage"], body=w["body"], today=GEN_DATE,
        )
        print(f"{code}: id={item.id}  error={item.error}  "
              f"problems={len(item.verify_problems or [])}  blocks_harvested={n}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    manifest = json.loads((RUNS_DIR / "ingest" / "manifest.json").read_text(encoding="utf-8"))
    codes = [m["code"] for m in manifest]
    (dry_run if args.dry_run else persist)(codes)
