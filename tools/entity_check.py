"""Corpus-global entity consistency check (Wave C2) — run anywhere, no LLM, no network.

Loads the entity registry (`grounding/entities/*.json`) and the whole in-repo corpus (the curated
Sachverhalt flagships + everything staged in the stores + the annotated texts), then runs the
deterministic cross-module lint (`teachersaid.pipeline.entity_lint`). It reports:

  * HARD problems  — a dangling entity_id, a linked year that contradicts the registry, or the same
                     entity linked to conflicting years across modules (the gate blocks these);
  * advisories     — a name that matches a registry alias but isn't linked (likely should be), and a
                     text whose author death-year disagrees with the registry;
  * shared entities — the "related modules" map (the verwandte_module joy).

    python tools/entity_check.py                # full report
    python tools/entity_check.py --strict       # exit 1 if any HARD problem (for CI/pre-commit)
    python tools/entity_check.py --json out.json # machine-readable digest

Facts (names/dates) are select-never-author: correct them in the registry JSON, never in prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Run-anywhere: import the teachersaid package sitting next to this tools/ dir (so a git worktree
# uses its own copy, not the editable-installed shared checkout).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from teachersaid.grounding import entities as ent
from teachersaid.pipeline import entity_lint as el


def _shared_entities(sachverhalte, texts, registry) -> list[dict]:
    """Every entity referenced by more than one module — the corpus-connective tissue."""
    out = []
    for e in ent.all_entities():
        rel = el.verwandte_module(e.entity_id, sachverhalte=sachverhalte, texts=texts,
                                  registry=registry)
        if len(rel) > 1:
            out.append({"entity_id": e.entity_id, "name": e.name, "modules": rel})
    return out


def build_report() -> dict:
    registry = ent.load_registry()
    sachverhalte, texts = el.gather_corpus()
    findings = el.scan_corpus(sachverhalte=sachverhalte, texts=texts, registry=registry)
    problems = el.problems(findings)
    return {
        "registry": {
            "count": len(registry),
            "kinds": dict(Counter(e.kind for e in registry.values())),
            "domains": {d: len(v) for d, v in ent.entities_by_domain().items()},
            "uncited": [e.entity_id for e in registry.values() if not (e.source and e.source.url)],
        },
        "corpus": {"sachverhalte": len(sachverhalte), "texts": len(texts)},
        "problems": [{"code": f.code, "module": f.module, "entity_id": f.entity_id,
                      "message": f.message} for f in problems],
        "warnings": [{"code": f.code, "module": f.module, "entity_id": f.entity_id,
                      "message": f.message} for f in findings if f.severity == "warning"],
        "shared_entities": _shared_entities(sachverhalte, texts, registry),
    }


def _print(rep: dict) -> None:
    r = rep["registry"]
    print(f"Entitäts-Register: {r['count']} Einträge  "
          f"({', '.join(f'{k}={v}' for k, v in sorted(r['kinds'].items()))})")
    print(f"  Domänen: {', '.join(f'{d}={n}' for d, n in sorted(r['domains'].items()))}")
    if r["uncited"]:
        print(f"  !! OHNE Quelle: {', '.join(r['uncited'])}")
    print(f"Korpus: {rep['corpus']['sachverhalte']} Sachverhalte, {rep['corpus']['texts']} Texte")

    print(f"\nHarte Probleme: {len(rep['problems'])}")
    for p in rep["problems"]:
        print(f"  [PROBLEM] {p['module']}: {p['message']}")
    print(f"\nHinweise (beratend): {len(rep['warnings'])}")
    for w in rep["warnings"]:
        print(f"  - {w['module']}: {w['message']}")

    print(f"\nGeteilte Entitäten (verwandte Module): {len(rep['shared_entities'])}")
    for s in rep["shared_entities"]:
        mods = ", ".join(f"{m['module_id']}[{m['via']}]" for m in s["modules"])
        print(f"  {s['name']} ({s['entity_id']}): {mods}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any HARD problem is found")
    ap.add_argument("--json", metavar="PATH", help="write the machine-readable digest here")
    args = ap.parse_args()

    try:                                    # UTF-8 output even when piped/redirected on Windows
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    rep = build_report()
    _print(rep)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=2)
        print(f"\n→ {args.json}")
    if args.strict and rep["problems"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
