"""Generate compact/extended scope variants of approved standard task blocks (Phase 3a).

`--build` writes a brief (`runs/ingest/variants/prompt_<CODE>.md`) listing the approved
standard task blocks of a target subject+Kompetenzbereich; a subagent produces, per
block, a `compact` and an `extended` GenTaskBlock (same competence/kind/dims/level/serves,
only the content richness + est_minutes differ) and writes
`runs/ingest/variants/<CODE>.json`. `--ingest` validates each through the real seam
(`orch.ingest_scope_variant`) and stores them (in_review, family=original id).

    python tools/scope_variants.py --build
    python tools/scope_variants.py --ingest runs/ingest/variants/PHY_STR.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.schema.richtext import plain_text
from teachersaid.store.blockstore import BlockStore

# demo target; add more (code, subject, kompetenzbereich) tuples to scale
TARGETS = [("PHY_STR", "Physik", "Strahlung und Radioaktivität")]


def _originals(subject: str, kb: str):
    return [b for b in BlockStore().approved()
            if b.role == "task" and b.subject == subject and b.kompetenzbereich == kb
            and b.scope == "standard" and not b.family]


def build_prompt(code: str, subject: str, kb: str) -> None:
    outdir = RUNS_DIR / "ingest" / "variants"
    outdir.mkdir(parents=True, exist_ok=True)
    origs = _originals(subject, kb)
    L = [
        f"# Scope-Varianten: {subject} — {kb}", "",
        "Erzeuge für **JEDEN** unten gelisteten Standard-Block je eine **compact**- und eine",
        "**extended**-Variante. Gleiche Kompetenz, gleicher `kind`, gleiche `dimensions`, gleiches",
        "`cognitive_level`, gleiches `serves` — es ändert sich nur der **Inhaltsumfang**:",
        "- **compact**: auf den Kern reduziert, weniger Teilaufgaben, kürzere `est_minutes`.",
        "- **extended**: reichhaltiger (mehr Teilschritte / Scaffolding / ein Beispiel), höhere `est_minutes`.",
        "Deutsch, AHS-Niveau. In JSON-Strings: „…“ oder \\\" verwenden — nie ein nacktes \" im Wert.", "",
        "## Originalblöcke (Standard-Variante)", "",
    ]
    for b in origs:
        t = b.block
        L.append(f"### {b.id}  · kind={b.kind} · level={b.cognitive_level} · dims={b.dimensions} "
                 f"· serves={b.competences} · ~{getattr(t, 'est_minutes', 0)} min")
        L.append(f"- prompt: {plain_text(t.prompt)}")
        if getattr(t, "answer_key", None):
            L.append(f"- answer_key: {plain_text(t.answer_key)}")
        L.append("")
    L += [
        "## Ausgabe", "",
        f"Schreibe **ausschließlich** dieses JSON nach `runs/ingest/variants/{code}.json` (kein Fließtext):",
        "```json",
        '[ {"original_id": "<id von oben>", "compact": <GenTaskBlock>, "extended": <GenTaskBlock>}, … ]',
        "```",
        "GenTaskBlock-Form (Schülertext ohne Kompetenz-IDs/„Lehrplan“):",
        '{"role":"task","id":"<id>","kind":"<kind>","prompt":"…","payload":null,'
        '"response":{"mode":"lines","n":3},"cognitive_level":"<level>","dimensions":[…],'
        '"serves":[{"competence_id":"<id>","relation":"exercises"}],"est_minutes":<int>,'
        '"answer_key":"…","watch_outs":["…"]}',
    ]
    (outdir / f"prompt_{code}.md").write_text("\n".join(L), encoding="utf-8")
    print(f"{code}: {len(origs)} standard blocks -> variants/prompt_{code}.json")


def ingest_variants(path: str) -> None:
    sys.path.insert(0, "tools")
    import ingest_batch as ib  # reuse the breadth normalizer (quote repair + slip fixes)
    from teachersaid.pipeline import orchestrator as orch

    entries = json.loads(ib._repair_text(Path(path).read_text(encoding="utf-8")), strict=False)
    bs = BlockStore()
    ok = bad = 0
    for e in entries:
        for scope in ("compact", "extended"):
            task = e.get(scope)
            if not task:
                continue
            ib._norm_block(task)
            _, problems = orch.ingest_scope_variant(bs, e["original_id"], scope, task)
            if problems:
                print(f"  {e['original_id']} {scope}: {problems[0]}")
                bad += 1
            else:
                ok += 1
    print(f"== {ok} variants stored (in_review), {bad} rejected ==")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--ingest")
    args = ap.parse_args()
    if args.ingest:
        ingest_variants(args.ingest)
    else:
        for code, subject, kb in TARGETS:
            build_prompt(code, subject, kb)
