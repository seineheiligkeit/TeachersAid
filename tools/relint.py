"""Re-run `verify` over every stored content item and refresh its findings.

A new lint (e.g. `pipeline/number_lint.py`) only runs when verify runs — items
staged BEFORE the lint existed carry stale `verify_warnings` and the dashboard
never shows the new findings. This tool re-verifies in place (status untouched:
re-linting never un-approves — the SME decides what to do with a finding).

    python tools/relint.py [--dry-run]
"""

from __future__ import annotations

import argparse

from teachersaid.pipeline.verify import verify
from teachersaid.store.repository import ReviewStore


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report, don't write")
    args = ap.parse_args()

    rs = ReviewStore()
    checked = changed = 0
    for it in rs.list(stage="content"):
        if it.content is None or it.resolution is None:
            continue
        checked += 1
        rep = verify(it.content, it.resolution)
        if rep.problems != it.verify_problems or rep.warnings != it.verify_warnings:
            changed += 1
            print(f"{it.id} [{it.status}]: {len(it.verify_warnings)} -> "
                  f"{len(rep.warnings)} warnings, {len(it.verify_problems)} -> "
                  f"{len(rep.problems)} problems")
            if not args.dry_run:
                it.verify_problems = rep.problems
                it.verify_warnings = rep.warnings
                rs.save(it)
    prefix = "DRY RUN — " if args.dry_run else ""
    print(f"{prefix}{checked} items re-verified, {changed} updated")


if __name__ == "__main__":
    main()
