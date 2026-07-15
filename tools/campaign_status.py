"""Status of an in-flight breadth pass — the babysitter for a fan-out generation run.

Given the gen dir a pass writes to, report per subject: how many of the expected N
worksheet files are present, load cleanly (through the SAME repair the ingest gate
applies, so a „…" quote slip reads as valid), and are already committed. The expected
(code, N) set comes from runs/ingest/manifest.json (written by breadth_prompt.py), or
override with --subjects/--n.

    python tools/campaign_status.py --dir runs/ingest/gen_us_2
    python tools/campaign_status.py --dir runs/ingest/gen_os_2 --subjects MAT,PHY --n 2

The authoritative validation is still `ingest_batch.py --dry-run`; this is the quick
"where is the batch" check while agents are still writing.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import ingest_batch as ib  # noqa: E402  — reuse the exact repair+load the gate uses


def _committed(path: Path) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)],
                       capture_output=True, cwd=REPO)
    return r.returncode == 0


def _expected(subjects: str | None, n: int) -> list[tuple[str, int]]:
    if subjects:
        return [(c.strip().upper(), n) for c in subjects.split(",") if c.strip()]
    manifest = RUNS_DIR / "ingest" / "manifest.json"
    if not manifest.exists():
        raise SystemExit("no manifest.json — pass --subjects explicitly")
    return [(e["code"], int(e.get("n", n))) for e in json.loads(manifest.read_text("utf-8"))]


def status(gen_dir: Path, expected: list[tuple[str, int]]) -> None:
    complete = partial = missing = invalid = 0
    print(f"{'subj':5} {'present':7} {'valid':5} {'commit':6}  state / sheets")
    print("-" * 68)
    for code, n in expected:
        files = [gen_dir / f"{code}_{i}.json" for i in range(1, n + 1)]
        present = [f for f in files if f.exists()]
        valids, bad = [], []
        for f in present:
            try:
                ib._load(f)
                valids.append(f)
            except Exception:  # noqa: BLE001
                bad.append(f)
        committed = sum(1 for f in valids if _committed(f))
        if len(valids) == n:
            state = "complete"; complete += 1
        elif valids:
            state = "partial"; partial += 1
        elif present:
            state = "INVALID"; invalid += 1
        else:
            state = "missing"; missing += 1
        sheets = " ".join(f.stem.split("_")[-1] + ("!" if f in bad else "") for f in present) or "—"
        print(f"{code:5} {len(present)}/{n:<5} {len(valids):<5} {committed}/{len(valids):<4}  {state}: {sheets}")
    total = len(expected)
    print(f"\n{complete} complete · {partial} partial · {missing} missing · {invalid} invalid "
          f"(of {total} subjects)")
    if invalid:
        print("→ INVALID files usually carry a „…\" quote slip the ingest normalizer repairs at "
              "load; the dry-run will confirm. Only re-generate if the dry-run also rejects it.")
    if missing or partial:
        gaps = [f"{c}" for c, n in expected
                if len([f for i in range(1, n + 1)
                        if (f := gen_dir / f'{c}_{i}.json').exists()]) < n]
        print(f"→ (re)generate incomplete subjects, then re-run: {', '.join(gaps)}")
    if complete == total:
        print(f"→ all present & valid. Next: python tools/ingest_batch.py --dry-run --dir {gen_dir}")


def main():
    ap = argparse.ArgumentParser(description="Status of an in-flight breadth pass.")
    ap.add_argument("--dir", required=True, help="the gen dir the pass writes to")
    ap.add_argument("--subjects", help="override expected codes (default: from manifest.json)")
    ap.add_argument("--n", type=int, default=2, help="expected files per subject")
    args = ap.parse_args()
    status(Path(args.dir), _expected(args.subjects, args.n))


if __name__ == "__main__":
    main()
