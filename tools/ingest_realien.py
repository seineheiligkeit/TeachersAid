"""Ingest subagent-authored Realien — the modern-FS breadth seam (Realien Phase 3).

A subagent authors a `Realie` JSON (a CONSTRUCTED, CEFR-leveled everyday text + a communicative
task layer — `Documents/realien-design.md`). This tool normalises the recurring agent slips,
validates through the real schema, runs the **internal-consistency lint** (`pipeline/realie_lint.py`
— a scan answer can't cite a time/price the Realie lacks; NOT world-grounding), derives the
worksheet (assemble → verify), and either reports (`--dry-run`) or stages it for HITL review
(`orch.ingest_text` + `compose_text_worksheet`). A constructed Realie rides **no rights gate**
(it's invented fiction); the SME fact-checks the **L2 and the level** at the gate — the one thing no
lint can.

    python tools/ingest_realien.py --dry-run --dir runs/ingest/realien
    python tools/ingest_realien.py --dir runs/ingest/realien        # stage into the stores
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
from teachersaid.pipeline.realie_lint import lint
from teachersaid.pipeline.text_tasks import build_worksheet
from teachersaid.pipeline.verify import verify
from teachersaid.schema.texts import AnnotatedText
from teachersaid.store.repository import ReviewStore
from teachersaid.store.textstore import TextStore

GEN_DATE = date(2026, 3, 1)
_AT_FIELDS = set(AnnotatedText.model_fields)
_KIND_FIX = {"scan": "comprehension", "read": "comprehension", "write": "communicative",
             "writing": "communicative", "speaking": "roleplay", "dialogue": "roleplay",
             "role_play": "roleplay", "role-play": "roleplay"}

# the German quote slip „…" (open U+201E, straight close) breaks the JSON string; repair only that
# closing " (the (?<!\\) guard leaves a correctly-escaped \" untouched).
_GERMAN_QUOTE_FIX = re.compile(r'„([^"„“”]*)(?<!\\)"')


def _repair_text(raw: str) -> str:
    return _GERMAN_QUOTE_FIX.sub(r'„\1“', raw)


def _normalize(at: dict) -> dict:
    """Absorb the recurring agent slips so well-formed CONTENT isn't lost to a key/shape slip."""
    at = {k: v for k, v in at.items() if k in _AT_FIELDS}    # drop stray top-level keys (extra=forbid)
    at.setdefault("origin", "constructed")
    at.setdefault("textsorte", "Realie")
    if at.get("origin") == "constructed":
        at.pop("source", None)                               # constructed fiction → no source
    for s in at.get("serves") or []:                         # a serves entry defaults to "exercises"
        if isinstance(s, dict):
            s.setdefault("relation", "exercises")
    for a in at.get("annotations") or []:
        if not isinstance(a, dict):
            continue
        if a.get("kind") in _KIND_FIX:                       # off-vocab kind → the canonical one
            a["kind"] = _KIND_FIX[a["kind"]]
        if a.get("roles") and not isinstance(a["roles"], list):
            a["roles"] = [a["roles"]]
        d = a.get("dimensions")
        if d and not isinstance(d, list):
            a["dimensions"] = [d]
    return at


def _load(path: Path) -> dict:
    raw = _repair_text(path.read_text(encoding="utf-8"))
    return _normalize(json.loads(raw, strict=False))         # tolerate literal control chars


def _check(path: Path):
    """(AnnotatedText | None, problems): JSON → schema → the internal-consistency lint."""
    try:
        data = _load(path)
    except Exception as e:                                   # noqa: BLE001
        return None, [f"JSON LOAD: {str(e)[:200]}"]
    try:
        at = AnnotatedText.model_validate(data)
    except Exception as e:                                   # noqa: BLE001
        return None, [f"SCHEMA: {str(e)[:300]}"]
    problems = [f"consistency: {p}" for p in lint(at)[0]]
    return at, problems


def dry_run(paths: list[Path]) -> None:
    ok = bad = 0
    for path in paths:
        at, problems = _check(path)
        if at is None:
            print(f"!! {path.stem}: {problems[0]}"); bad += 1; continue
        nt = 0
        try:
            content, res = build_worksheet(at, today=GEN_DATE)
            assemble(content, res)
            problems += [f"verify: {p}" for p in verify(content, res).problems]
            nt = sum(1 for b in content.iter_blocks() if b.role.value == "task")
        except Exception as e:                               # noqa: BLE001
            problems.append(f"BUILD/VERIFY RAISED: {type(e).__name__}: {str(e)[:200]}")
        flag = "OK " if not problems else "!! "
        print(f"{flag}{path.stem}: „{at.title[:34]}“ {at.subject[:22]} kl{at.klasse} "
              f"{at.cefr} {at.origin} · annos={len(at.annotations)} tasks={nt} "
              f"facts={len(at.facts)} · problems={len(problems)}")
        for p in problems:
            print("       ", p)
        ok += not problems
        bad += bool(problems)
    print(f"\n== {ok} clean, {bad} need attention, {len(paths)} total ==")


def persist(paths: list[Path]) -> None:
    textstore, review = TextStore(), ReviewStore()
    staged = 0
    for path in paths:
        at, problems = _check(path)
        if at is None or problems:
            print(f"SKIP {path.stem}: {(problems or ['?'])[0]}")
            continue
        orch.ingest_text(textstore, at, source="generated", today=GEN_DATE)
        item = orch.compose_text_worksheet(review, textstore, at.id, today=GEN_DATE)
        staged += 1
        print(f"{path.stem}: {at.id} → item={item.id} error={item.error} "
              f"problems={len(item.verify_problems or [])}")
    print(f"\n== staged {staged}/{len(paths)} Realien (Texte-Tab + Inhalte) ==")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dir", default=str(RUNS_DIR / "ingest" / "realien"))
    args = ap.parse_args()
    paths = sorted(Path(args.dir).glob("*.json"))
    (dry_run if args.dry_run else persist)(paths)
