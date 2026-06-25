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
import re
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
_INFO_KEYS = {"role", "id", "kind", "content", "callout_role", "teacher_note",
              "watch_outs", "optional", "modality", "asset_refs", "flags"}
_VALID_INFO_KINDS = {"prose", "key_fact", "example", "procedure", "figure",
                     "data_reference", "callout"}
_ANSWER_ALIASES = ("answer_text", "loesung", "lösung", "loesungsvorschlag", "musterloesung")


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


def _norm_block(b: dict) -> None:
    """Coerce one block to the generation-view schema (in place)."""
    if b.get("role") == "info":
        if "content" not in b and "prompt" in b:   # agent shaped an info block like a task
            b["content"] = b.pop("prompt")
        if b.get("kind") not in _VALID_INFO_KINDS:  # e.g. "text" -> prose
            b["kind"] = "prose"
        for k in [k for k in b if k not in _INFO_KEYS]:  # drop est_minutes/response/etc.
            b.pop(k, None)
        return
    for alias in _ANSWER_ALIASES:                   # answer_text/Lösung -> answer_key
        if alias in b and not b.get("answer_key"):
            b["answer_key"] = b.pop(alias)
        else:
            b.pop(alias, None)
    p = b.get("payload")                            # nested multi-question MC (options as
    if isinstance(p, dict) and p.get("kind") == "multiple_choice":  # {question,options} dicts)
        opts = p.get("options") or []                # -> fold the questions into the prompt
        if any(isinstance(o, dict) for o in opts):
            folded = []
            for o in opts:
                if isinstance(o, dict):
                    q = o.get("question") or o.get("frage") or ""
                    subs = o.get("options") or o.get("choices") or []
                    folded.append(q + ("  (" + " / ".join(map(str, subs)) + ")" if subs else ""))
                else:
                    folded.append(str(o))
            b["prompt"] = (b.get("prompt", "") + "\n\n" + "\n".join(folded)).strip()
            b["payload"] = None
    for s in b.get("serves", []):                   # only exercises/builds_prerequisite valid
        if s.get("relation") not in _VALID_RELATIONS:
            s["relation"] = "exercises"
    rub = b.get("rubric")
    if isinstance(rub, list):                        # German keys + rich level objects
        fixed = []
        for r in rub:
            r = {_RUBRIC_KEYMAP.get(k, k): v for k, v in r.items()}
            if isinstance(r.get("levels"), list):
                r["levels"] = [_stringify_level(lv) for lv in r["levels"]]
            fixed.append(r)
        b["rubric"] = fixed


def _normalize(body: dict) -> dict:
    for b in body.get("intro", []):
        _norm_block(b)
    for sec in body.get("sections", []):
        for b in sec.get("blocks", []):
            _norm_block(b)
    return body


# A German quote span opened with „ but CLOSED with a straight " breaks the JSON
# string (the bare " terminates it). Convert ONLY that closing " to the typographic “.
# The content class excludes every quote variant so the match can't run past a proper
# typographic close to the structural quote (which would corrupt valid JSON).
_GERMAN_QUOTE_FIX = re.compile(r'„([^"„“”]*)(?<!\\)"')


def _repair_text(raw: str) -> str:
    """Repair the agent JSON slip „…" (typographic open U+201E, straight close).
    The (?<!\\) guard leaves a correctly-escaped \\" untouched."""
    return _GERMAN_QUOTE_FIX.sub(r'„\1“', raw)


def _load(path) -> dict:
    raw = _repair_text(path.read_text(encoding="utf-8"))
    w = json.loads(raw, strict=False)  # tolerate literal control chars (raw newlines) in strings
    w["body"] = _normalize(w["body"])
    return w


def _resolution(w: dict):
    subj, kl = w["subject"], w["klasse"]
    kb = w.get("kompetenzbereich")
    if kb:
        return resolve_kompetenzbereich(subj, kl, kb, today=GEN_DATE)
    return resolve_grade(subj, kl, today=GEN_DATE)


def dry_run(paths: list) -> None:
    ok = bad = 0
    for path in paths:
        name = path.stem
        try:
            w = _load(path)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: JSON LOAD ERROR: {str(e)[:200]}"); bad += 1; continue
        res = _resolution(w)
        model = ls.get_subject_model(w["subject"])
        try:
            gb = GenWorksheetBody.model_validate(w["body"])
        except Exception as e:  # noqa: BLE001
            print(f"{name}: SCHEMA ERROR: {str(e)[:300]}"); bad += 1; continue
        meta = WorksheetMeta(
            title=w["title"], subject=w["subject"], stufe="Unterstufe", klasse=w["klasse"],
            kernfrage=w["kernfrage"], fassung=res.fassung,
            lehrplan_label=f"{w['subject']} · {w['klasse']}. Kl. · "
                           f"{w.get('kompetenzbereich') or w.get('scope_label')}",
        )
        if w.get("kompetenzbereich"):  # mirror ingest_generated's cross-KB widening
            served = {s.competence_id for sec in gb.sections for b in sec.blocks
                      for s in getattr(b, "serves", [])}
            if served - {c.id for c in res.competences}:
                gres = resolve_grade(w["subject"], w["klasse"], today=GEN_DATE)
                if served <= {c.id for c in gres.competences}:
                    res = gres
        content = body_to_canonical(gb, meta=meta, subject_model=model)
        try:
            assemble(content, res)
            rep = verify(content, res)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: ASSEMBLE/VERIFY RAISED: {type(e).__name__}: {str(e)[:300]}"); bad += 1; continue
        nt = sum(1 for b in content.iter_blocks() if b.role == "task")
        cov = content.nachweis.competence_coverage
        flag = "OK " if not rep.problems else "!! "
        print(f"{flag}{name}: '{w['title'][:48]}' kl{w['klasse']} tasks={nt} "
              f"problems={len(rep.problems)} warnings={len(rep.warnings)} "
              f"coverage={sum(c.covered for c in cov)}/{len(cov)}")
        for p in rep.problems:
            print("      PROBLEM:", p)
        ok += not rep.problems
        bad += bool(rep.problems)
    print(f"\n== {ok} clean, {bad} need attention, {len(paths)} total ==")


def persist(paths: list) -> None:
    store, blocks = ReviewStore(), BlockStore()
    total = 0
    for path in paths:
        w = _load(path)
        item, n = orch.ingest_generated(
            store, blocks, w["subject"], w["klasse"],
            kompetenzbereich=w.get("kompetenzbereich"), scope_label=w.get("scope_label"),
            title=w["title"], kernfrage=w["kernfrage"], body=w["body"], render=False, today=GEN_DATE,
        )
        total += n
        print(f"{path.stem}: id={item.id} error={item.error} "
              f"problems={len(item.verify_problems or [])} blocks={n}")
    print(f"\n== staged {len(paths)} worksheets, {total} blocks harvested ==")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dir", default=str(RUNS_DIR / "ingest" / "gen"))
    args = ap.parse_args()
    from pathlib import Path
    paths = sorted(Path(args.dir).glob("*.json"))
    (dry_run if args.dry_run else persist)(paths)
