"""Fit + persist the C4 difficulty model, and report its (honest) quality.

Deterministic, offline, no LLM. Reads the approved+in_review block corpus (the BlockStore),
computes the transparent feature vector (`pipeline/difficulty_model.features`) and the
*effective* difficulty label (`pipeline/difficulty.effective_difficulty` — authored 1–3 if
set, else the cognitive-level band) for every task block, then:

  * fits the TWO thresholds of the ordinal model by exhaustive grid search over the corpus
    scores (the weights are CURATED, not learned — see `difficulty_model.CURATED_WEIGHTS`
    and the module docstring for why a difficulty model is not learnable from this corpus);
  * writes the versioned model to `teachersaid/pipeline/difficulty_weights.json`;
  * prints the fit report: label distribution, exact/adjacent accuracy, the confusion
    matrix, the per-feature weight table, and the size of the ≥1-band review-cue list.

    python tools/fit_difficulty.py            # fit + write + report
    python tools/fit_difficulty.py --dry-run  # report only, don't write the JSON
    python tools/fit_difficulty.py --check    # verify the shipped JSON is up to date (CI)

The reported numbers are the ones quoted in `Documents/difficulty-model.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # import the worktree's teachersaid, not a site egg-link

from teachersaid.pipeline import difficulty_model as dm  # noqa: E402
from teachersaid.pipeline.difficulty import effective_difficulty  # noqa: E402
from teachersaid.store.blockstore import BlockStore  # noqa: E402

MODEL_VERSION = 1
JSON_PATH = REPO_ROOT / "teachersaid" / "pipeline" / "difficulty_weights.json"


def _score(feats: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights.get(k, 0.0) * feats[k] for k in dm.FEATURE_NAMES)


def _fit_thresholds(scored: list[tuple[float, int]]) -> tuple[float, float]:
    """Two thresholds maximizing exact agreement with the label, by an O(n²) prefix-count
    scan over sorted scores (deterministic; ties broken by the lowest cut index)."""
    sl = sorted(scored, key=lambda x: x[0])
    scores = [s for s, _ in sl]
    labels = [l for _, l in sl]
    n = len(sl)
    pref = {c: [0] * (n + 1) for c in (1, 2, 3)}
    for k in range(n):
        for c in (1, 2, 3):
            pref[c][k + 1] = pref[c][k]
        pref[labels[k]][k + 1] += 1
    best = (-1, 0, 0)
    for i in range(n + 1):
        c1 = pref[1][i]
        for j in range(i, n + 1):
            acc = c1 + (pref[2][j] - pref[2][i]) + (pref[3][n] - pref[3][j])
            if acc > best[0]:
                best = (acc, i, j)
    _, i, j = best

    def cut(k: int) -> float:
        if k == 0:
            return round(scores[0] - 0.01, 4)
        if k == n:
            return round(scores[-1] + 0.01, 4)
        return round((scores[k - 1] + scores[k]) / 2, 4)

    return cut(i), cut(j)


def _load_corpus() -> list[tuple[object, dict[str, float], int]]:
    """Every task block in the corpus → (block, features, effective-difficulty label)."""
    store = BlockStore()
    rows = []
    for lb in store.list():
        feats = dm.features(lb.block)
        if feats is None:          # info blocks carry no difficulty
            continue
        rows.append((lb, feats, effective_difficulty(lb.block)))
    return rows


def _report(rows, weights, t1, t2) -> dict:
    n = len(rows)
    exact = adj = 0
    conf = {(a, b): 0 for a in (1, 2, 3) for b in (1, 2, 3)}
    disagreements = []
    for lb, feats, label in rows:
        s = _score(feats, weights)
        pred = dm.band_for_score(s, (t1, t2))
        conf[(label, pred)] += 1
        exact += pred == label
        adj += abs(pred - label) <= 1
        if abs(pred - label) >= 1:
            disagreements.append((lb.id, label, pred))
    return {
        "n": n,
        "label_dist": {b: sum(1 for _, _, l in rows if l == b) for b in (1, 2, 3)},
        "exact": exact / n,
        "adjacent": adj / n,
        "confusion": conf,
        "disagreements": disagreements,
    }


def _build_model(weights, t1, t2, rep) -> dict:
    return {
        "version": MODEL_VERSION,
        "generated": date.today().isoformat(),
        "method": "curated anchor-and-nudge weights; thresholds fit by grid search on the "
                  "effective-difficulty label (see tools/fit_difficulty.py, "
                  "Documents/difficulty-model.md)",
        "feature_order": list(dm.FEATURE_NAMES),
        "weights": {k: weights[k] for k in dm.FEATURE_NAMES},
        "thresholds": [t1, t2],
        "normalization": {
            "STEP_CAP": dm.STEP_CAP, "MATH_CAP": dm.MATH_CAP,
            "WSTF_FLOOR": dm.WSTF_FLOOR, "WSTF_CEIL": dm.WSTF_CEIL,
            "TEXT_NEUTRAL": dm.TEXT_NEUTRAL,
        },
        "fit": {
            "corpus_blocks": rep["n"],
            "label_distribution": rep["label_dist"],
            "exact_accuracy": round(rep["exact"], 4),
            "adjacent_accuracy": round(rep["adjacent"], 4),
            "review_cue_count": len(rep["disagreements"]),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report only; don't write JSON")
    ap.add_argument("--check", action="store_true",
                    help="fail if the shipped JSON differs from a fresh fit (CI guard)")
    args = ap.parse_args()

    weights = dict(dm.CURATED_WEIGHTS)
    rows = _load_corpus()
    if not rows:
        print("no task blocks found in the corpus — nothing to fit", file=sys.stderr)
        sys.exit(1)
    scored = [(_score(f, weights), l) for _, f, l in rows]
    t1, t2 = _fit_thresholds(scored)
    rep = _report(rows, weights, t1, t2)
    model = _build_model(weights, t1, t2, rep)

    # --- report -------------------------------------------------------------
    print(f"corpus: {rep['n']} task blocks   label dist (effective difficulty): "
          f"{rep['label_dist']}")
    print(f"thresholds (fit): t1={t1}  t2={t2}")
    print(f"exact agreement:    {rep['exact']:.3f}")
    print(f"adjacent agreement: {rep['adjacent']:.3f}")
    print(f"review cues (|est - effective| >= 1 band): {len(rep['disagreements'])} "
          f"({100 * len(rep['disagreements']) / rep['n']:.1f}%)")
    print("confusion (true -> pred):")
    for tl in (1, 2, 3):
        print(f"  band {tl}: " + "  ".join(
            f"{p}:{rep['confusion'][(tl, p)]:>4}" for p in (1, 2, 3)))
    print("weights (curated; all positive - each feature raises difficulty):")
    for k in dm.FEATURE_NAMES:
        print(f"  {k:<7} {weights[k]:.2f}")

    new_json = json.dumps(model, ensure_ascii=False, indent=2)
    if args.check:
        current = JSON_PATH.read_text(encoding="utf-8") if JSON_PATH.exists() else ""
        # compare ignoring the volatile `generated` date
        def _norm(txt):
            try:
                d = json.loads(txt); d.pop("generated", None); return d
            except Exception:
                return None
        if _norm(current) == _norm(new_json):
            print("\n[check] shipped JSON is up to date.")
        else:
            print("\n[check] shipped JSON is STALE — re-run without --check.", file=sys.stderr)
            sys.exit(2)
        return

    if args.dry_run:
        print("\n[dry-run] not writing", JSON_PATH)
        return
    JSON_PATH.write_text(new_json, encoding="utf-8")
    print("\nwrote", JSON_PATH.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
