"""Ingest subagent-authored Sachverhalt modules — the content-layer breadth pattern.

A subagent authors a `Sachverhalt` JSON (structured, SOURCED facts + a Darstellung over them,
anchored to real catalog competences). This tool normalises the recurring agent JSON slips,
validates through the real schema, runs the **facts gate** (≥1 `role="facts"` source) + the
deterministic **entity-lint** (every year in the Darstellung must be in the fact-set), derives the
worksheet (assemble → verify), and either reports (`--dry-run`) or stages it for HITL review
(`orch.ingest_sachverhalt` + `compose_sachverhalt_worksheet`).

The facts are *selected/sourced*; the Darstellung is *authored-then-vetted*; nothing is invented
that the entity-lint can catch, and the SME fact-checks the rest at the gate.

    python tools/ingest_sachverhalte.py --dry-run --dir runs/ingest/sv
    python tools/ingest_sachverhalte.py --dir runs/ingest/sv        # stage into the store
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
from teachersaid.pipeline.sachverhalt import build_worksheet
from teachersaid.pipeline.sachverhalt_lint import lint
from teachersaid.pipeline.verify import verify
from teachersaid.schema.sachverhalt import Sachverhalt
from teachersaid.store.repository import ReviewStore
from teachersaid.store.sachverhaltstore import SachverhaltStore

GEN_DATE = date(2026, 3, 1)            # inside the Fassung window; deterministic
_CAUSAL_KINDS = {"voraussetzung", "ursache", "verlauf", "folge", "wirkung"}
_SV_FIELDS = set(Sachverhalt.model_fields)

# the German quote slip „…" (typographic open U+201E, straight close) breaks the JSON string;
# repair ONLY that closing " (the (?<!\\) guard leaves a correctly-escaped \" untouched).
_GERMAN_QUOTE_FIX = re.compile(r'„([^"„“”]*)(?<!\\)"')


def _repair_text(raw: str) -> str:
    return _GERMAN_QUOTE_FIX.sub(r'„\1“', raw)


def _normalize(sv: dict) -> dict:
    """Absorb the recurring agent slips so well-formed CONTENT isn't lost to a key slip."""
    sv = {k: v for k, v in sv.items() if k in _SV_FIELDS}    # drop stray top-level keys (extra=forbid)
    kr = sv.get("klasse_range")
    if isinstance(kr, int):                                  # a single grade → a 1-grade range
        sv["klasse_range"] = [kr, kr]
    for s in sv.get("sources") or []:                        # a source defaults to role="facts"
        if isinstance(s, dict) and not s.get("role"):
            s["role"] = "facts"
    for c in sv.get("causes") or []:                         # off-enum causal kind → "folge"
        if isinstance(c, dict) and c.get("kind") not in _CAUSAL_KINDS:
            c["kind"] = "folge"
    for d in sv.get("darstellung") or []:
        if isinstance(d, dict):
            d.setdefault("grounded_by", [])
            d.pop("provenance", None)                        # the derivation attaches it; don't author
    return sv


def _load(path: Path) -> dict:
    raw = _repair_text(path.read_text(encoding="utf-8"))
    return _normalize(json.loads(raw, strict=False))         # tolerate literal control chars


def _check(path: Path):
    """(Sachverhalt | None, problems): JSON → schema → facts gate + entity-lint."""
    try:
        data = _load(path)
    except Exception as e:                                   # noqa: BLE001
        return None, [f"JSON LOAD: {str(e)[:200]}"]
    try:
        sv = Sachverhalt.model_validate(data)
    except Exception as e:                                   # noqa: BLE001
        return None, [f"SCHEMA: {str(e)[:300]}"]
    problems: list[str] = []
    if not sv.facts_sources():
        problems.append("facts gate: keine role='facts'-Quelle")
    lint_problems, _warnings = lint(sv)
    problems += [f"entity-lint: {p}" for p in lint_problems]
    return sv, problems


def dry_run(paths: list[Path]) -> None:
    ok = bad = 0
    for path in paths:
        sv, problems = _check(path)
        if sv is None:
            print(f"!! {path.stem}: {problems[0]}")
            bad += 1
            continue
        nt = 0
        try:
            content, res = build_worksheet(sv, today=GEN_DATE)
            assemble(content, res)
            problems += [f"verify: {p}" for p in verify(content, res).problems]
            nt = sum(1 for b in content.iter_blocks() if b.role.value == "task")
        except Exception as e:                               # noqa: BLE001
            problems.append(f"BUILD/VERIFY RAISED: {type(e).__name__}: {str(e)[:200]}")
        flag = "OK " if not problems else "!! "
        print(f"{flag}{path.stem}: „{sv.topic[:42]}“ {sv.subject[:16]} kl{tuple(sv.klasse_range)} "
              f"· tl={len(sv.timeline)} proc={len(sv.process)} reg={len(sv.regions)} "
              f"caus={len(sv.causes)} konz={len(sv.concepts)} tasks={nt} · problems={len(problems)}")
        for p in problems:
            print("       ", p)
        ok += not problems
        bad += bool(problems)
    print(f"\n== {ok} clean, {bad} need attention, {len(paths)} total ==")


def persist(paths: list[Path]) -> None:
    svstore, review = SachverhaltStore(), ReviewStore()
    staged = 0
    for path in paths:
        sv, problems = _check(path)
        if sv is None or problems:
            print(f"SKIP {path.stem}: {(problems or ['?'])[0]}")
            continue
        orch.ingest_sachverhalt(svstore, sv, source="generated")
        item = orch.compose_sachverhalt_worksheet(review, svstore, sv.id, today=GEN_DATE)
        staged += 1
        print(f"{path.stem}: {sv.id} → item={item.id} error={item.error} "
              f"problems={len(item.verify_problems or [])}")
    print(f"\n== staged {staged}/{len(paths)} Sachverhalte (Sachverhalte-Tab + Inhalte) ==")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dir", default=str(RUNS_DIR / "ingest" / "sv"))
    args = ap.parse_args()
    paths = sorted(Path(args.dir).glob("*.json"))
    (dry_run if args.dry_run else persist)(paths)
