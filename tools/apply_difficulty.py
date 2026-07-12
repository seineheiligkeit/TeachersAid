"""Apply SME-accepted difficulty labels onto the block corpus (the C4 apply step).

Deterministic, offline, no LLM — and **SME-run, never automatic**: this is the second half
of the authored-then-SME-vetted loop started by `tools/propose_difficulty.py`. The SME
edits `runs/difficulty/difficulty_proposals.json` (set `accepted: true` to take a
proposal's `proposed_difficulty`, edit the band first if needed, `false` to discard) and
then runs this tool. Nothing else ever writes authored difficulty.

What it does, in order:

  1. loads the proposals JSON and VALIDATES every accepted proposal up front — an unknown
     block id, a non-task block, a band outside 1–3, or a non-boolean `accepted` value is
     a hard failure and NOTHING is applied (fail-fast, no partial surprises);
  2. prints the full plan (which blocks get which band; which are already set);
  3. unless `--dry-run`, sets `block.difficulty` on each accepted block and saves through
     the BlockStore's `upsert` — which preserves review status and `created_at` by
     construction (re-labelling never un-approves anything);
  4. records provenance the light way: stamps `applied_at` on each applied proposal and
     appends an `applications` log entry in the proposals file itself (the file lives in
     runs/ — git-owned, diffable text; no new store, no feedback-digest noise).

Idempotent: a re-run finds every accepted band already on its block and applies nothing.

    python tools/apply_difficulty.py                          # default proposals path
    python tools/apply_difficulty.py path/to/proposals.json   # explicit file
    python tools/apply_difficulty.py --dry-run                # plan only, write nothing

After applying, re-run `python tools/fit_difficulty.py` — with authored labels that
diverge from the cognitive fallback, the C4 model becomes genuinely evaluable
(`Documents/difficulty-model.md`).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # import the worktree's teachersaid, not a site egg-link

from teachersaid.store.blockstore import BlockStore  # noqa: E402

DEFAULT_PROPOSALS = REPO_ROOT / "runs" / "difficulty" / "difficulty_proposals.json"
KNOWN_VERSIONS = (1,)


class ApplyError(Exception):
    """A validation failure — raised BEFORE anything is written (fail-fast, all-or-nothing)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- validation (all-or-nothing: any error here means zero writes) ------------------------

def validate(doc: dict, store: BlockStore) -> list[dict]:
    """Check the document shape and every proposal; return the accepted subset.

    Hard-fails (ApplyError) on: unknown schema version, a missing proposals list, an
    `accepted` value that is not true/false/null (an SME edit slip must not be silently
    skipped), an accepted proposal whose band is not 1-3, whose block id is unknown in
    the store, or whose block is not a task block.
    """
    if doc.get("version") not in KNOWN_VERSIONS:
        raise ApplyError(f"unknown proposals version {doc.get('version')!r} "
                         f"(known: {list(KNOWN_VERSIONS)})")
    proposals = doc.get("proposals")
    if not isinstance(proposals, list):
        raise ApplyError("proposals file carries no 'proposals' list")

    errors: list[str] = []
    accepted: list[dict] = []
    for i, p in enumerate(proposals):
        if not isinstance(p, dict):
            errors.append(f"<proposal #{i}>: not an object")
            continue
        bid = p.get("block_id", f"<proposal #{i}>")
        acc = p.get("accepted")
        if acc not in (True, False, None):
            errors.append(f"{bid}: accepted={acc!r} is not true/false/null "
                          f"(edit slip? nothing was applied)")
            continue
        if acc is not True:
            continue
        band = p.get("proposed_difficulty")
        if band not in (1, 2, 3):
            errors.append(f"{bid}: proposed_difficulty={band!r} is not 1, 2 or 3")
            continue
        lb = store.get(bid)
        if lb is None:
            errors.append(f"{bid}: unknown block id (not in the blockstore)")
            continue
        if lb.role != "task":
            errors.append(f"{bid}: not a task block (difficulty is a task property)")
            continue
        accepted.append(p)
    if errors:
        raise ApplyError("validation failed — NOTHING applied:\n  " + "\n  ".join(errors))
    return accepted


# --- apply --------------------------------------------------------------------------------

def apply_proposals(doc: dict, store: BlockStore, *, dry_run: bool = False) -> dict:
    """Validate, then apply every `accepted: true` proposal's band onto its block.

    Returns a summary dict. Mutates `doc` (stamps `applied_at` on applied proposals and
    appends an `applications` log entry) only on a real, non-empty apply — the caller
    persists the file. Idempotent: a band already on the block is counted as
    `already_set` and not re-written (its first `applied_at` stays).
    """
    accepted = validate(doc, store)
    proposals = doc.get("proposals", [])

    to_apply: list[tuple[dict, object]] = []
    already: list[dict] = []
    for p in accepted:
        lb = store.get(p["block_id"])
        if getattr(lb.block, "difficulty", None) == p["proposed_difficulty"]:
            already.append(p)
        else:
            to_apply.append((p, lb))

    applied: list[dict] = []
    if not dry_run:
        stamp = _now()
        for p, lb in to_apply:
            lb.block.difficulty = p["proposed_difficulty"]
            store.upsert(lb)               # preserves review status + created_at by construction
            p["applied_at"] = stamp
            applied.append(p)
        if applied:
            doc.setdefault("applications", []).append({
                "at": stamp,
                "applied": len(applied),
                "already_set": len(already),
                "tool": "tools/apply_difficulty.py",
            })
    else:
        applied = [p for p, _ in to_apply]

    return {
        "dry_run": dry_run,
        "total_proposals": len(proposals),
        "accepted": len(accepted),
        "applied": [p["block_id"] for p in applied],
        "already_set": [p["block_id"] for p in already],
        "skipped_null": sum(1 for p in proposals if p.get("accepted") is None),
        "rejected": sum(1 for p in proposals if p.get("accepted") is False),
        "doc_changed": bool(applied) and not dry_run,
    }


def apply_file(path: Path, store: BlockStore | None = None, *,
               dry_run: bool = False) -> dict:
    """Load → apply → write the provenance-stamped file back (only if something applied)."""
    store = store or BlockStore()
    doc = json.loads(path.read_text(encoding="utf-8"))
    summary = apply_proposals(doc, store, dry_run=dry_run)
    if summary["doc_changed"]:
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


# --- CLI ----------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proposals", nargs="?", type=Path, default=DEFAULT_PROPOSALS,
                    help=f"proposals JSON (default: {DEFAULT_PROPOSALS.relative_to(REPO_ROOT)})")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan; write neither blocks nor the proposals file")
    args = ap.parse_args()

    if not args.proposals.exists():
        print(f"proposals file not found: {args.proposals}", file=sys.stderr)
        sys.exit(1)

    store = BlockStore()
    doc = json.loads(args.proposals.read_text(encoding="utf-8"))
    try:
        accepted = validate(doc, store)
    except ApplyError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    # --- the plan, always printed first --------------------------------------------------
    proposals = doc.get("proposals", [])
    print(f"proposals: {len(proposals)} total — {len(accepted)} accepted, "
          f"{sum(1 for p in proposals if p.get('accepted') is False)} rejected, "
          f"{sum(1 for p in proposals if p.get('accepted') is None)} undecided (accepted=null)")
    if not accepted:
        print("nothing accepted — nothing to apply. (Set accepted: true in the JSON first.)")
        return
    for p in accepted:
        lb = store.get(p["block_id"])
        current = getattr(lb.block, "difficulty", None)
        state = "already set" if current == p["proposed_difficulty"] else f"{current} -> {p['proposed_difficulty']}"
        print(f"  {p['block_id']:<28} difficulty {state}   "
              f"({p.get('subject', '?')}, {p.get('kind', '?')}, status={lb.status})")

    summary = apply_proposals(doc, store, dry_run=args.dry_run)
    if args.dry_run:
        print(f"\n[dry-run] would apply {len(summary['applied'])}, "
              f"already set {len(summary['already_set'])} — nothing written")
        return
    if summary["doc_changed"]:
        args.proposals.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    print(f"\napplied {len(summary['applied'])}, already set {len(summary['already_set'])}, "
          f"skipped (accepted=null) {summary['skipped_null']}, rejected {summary['rejected']}")
    if summary["applied"]:
        print("provenance stamped into", args.proposals)
        print("next: re-run  python tools/fit_difficulty.py  — the model is now evaluable "
              "against authored labels.")


if __name__ == "__main__":
    main()
