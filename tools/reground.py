"""Re-ground the (c)-label-flagged GWB worksheet figures (one-off migration).

The three tracked content items c0081 / c0096 / c0097 carried data figures with
real-looking numbers but no `data_source` and no `illustrative` flag — the (c)-label
gate (`pipeline/figure_lint`) warns on exactly that. This helper attaches, per figure,
either a `data_source` (→ real values + citation filled by `ground_data` at assemble) or
`illustrative=True` (honestly schematic figures we do not source), applies the *minimal*
task-text edits a changed number forces, then re-runs the real assemble→verify seam and
saves the item back to the store. Every text edit asserts its target substring is present,
so a stale string fails loudly instead of silently no-op-ing.

    python tools/reground.py            # apply + save
    python tools/reground.py --dry-run  # report only, don't save

Deterministic, offline (the datasets are curated in grounding/data/); no LLM.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # import the worktree's teachersaid, not a site egg-link

from teachersaid.pipeline.assemble import assemble  # noqa: E402
from teachersaid.pipeline.verify import verify  # noqa: E402
from teachersaid.schema.datasets import DataRef  # noqa: E402
from teachersaid.store.repository import ReviewStore  # noqa: E402

CLABEL = "ohne Quellenangabe"  # the figure_lint (c)-label warning fragment

# --- per-item plan: figure grounding + the task-text edits a changed number forces --------
# asset ops: {"source": (dataset_id, series)}  OR  {"illustrative": True};  "title" retitles spec.
# text edits: (block_id, field, old, new) for a task/info block field (str or list[str]);
#             ("@tp", section_id, old, new) for a section teacher_overview talking point.
PLAN: dict[str, dict] = {
    "c0081": {
        "assets": {
            "abb1": {"source": ("un_wpp_kontinente_2024", "kontinente")},
            "abb2": {"source": ("worldbank_urbanisierung", "welt_verlauf"),
                     "title": "Anteil der Stadtbevölkerung an der Weltbevölkerung (%)"},
            "abb3": {"source": ("worldbank_fertilitaet", "vergleich")},
        },
        "edits": [
            ("t1", "answer_key",
             "a) Asien mit ca. 4,79 Mrd. Menschen. b) Summe aller Werte ≈ 8,07 Mrd.",
             "a) Asien mit ca. 4,81 Mrd. Menschen. b) Summe aller Werte ≈ 8,16 Mrd."),
            ("t1", "prompt",
             "aber mehr als doppelt so viele Einwohner:innen",
             "aber fast doppelt so viele Einwohner:innen"),
            ("t2", "answer_key",
             "Raten zwischen ca. 5,2 und 6,8, europäische Länder zwischen ca. 0,78 und 1,58",
             "Raten zwischen ca. 5,0 und 6,0, europäische Länder zwischen ca. 0,75 und 1,4"),
            ("t2", "watch_outs",
             "Südkoreas Wert (0,78) ist der niedrigste der Welt",
             "Südkoreas Wert (0,75) ist der niedrigste der Welt"),
            ("t3", "prompt",
             "an der Weltbevölkerung seit 1950 entwickelt hat",
             "an der Weltbevölkerung seit 1960 entwickelt hat"),
            ("t3", "prompt",
             "b) Was bedeutet es, wenn 2050 laut Prognose 68 % der Menschen in Städten leben? "
             "Nenne zwei mögliche Herausforderungen und zwei mögliche Vorteile des Stadtlebens.",
             "b) Aktuell (2023) leben rund 57 % der Menschen in Städten – Tendenz weiter steigend. "
             "Nenne zwei mögliche Herausforderungen und zwei mögliche Vorteile des Stadtlebens."),
            ("t3", "answer_key",
             "a) Kontinuierlicher Anstieg von 29 % (1950) auf 57 % (2024); Prognose 68 % für 2050 "
             "– der Trend setzt sich fort.",
             "a) Kontinuierlicher Anstieg von rund 34 % (1960) auf rund 57 % (2023) "
             "– der Trend setzt sich fort."),
            ("@tp", "s2",
             "Urbanisierung als globaler Megatrend: 2024 lebt erstmals mehr als die Hälfte der "
             "Weltbevölkerung in Städten.",
             "Urbanisierung als globaler Megatrend: seit rund 2008 lebt mehr als die Hälfte der "
             "Weltbevölkerung in Städten (2023 rund 57 %)."),
        ],
    },
    "c0096": {
        "assets": {
            "abb1": {"source": ("noaa_co2_mauna_loa", "verlauf")},
            "abb2": {"illustrative": True},
            "abb3": {"illustrative": True},
        },
        "edits": [
            ("t1", "answer_key",
             "von ca. 317 ppm (1960) auf ca. 422 ppm (2024), also um über 100 ppm in 64 Jahren. "
             "Der Anstieg ist im Vergleich 2000–2024 am stärksten (ca. 52 ppm in 24 Jahren "
             "gegenüber ca. 37 ppm in den ersten 30 Jahren).",
             "von ca. 317 ppm (1960) auf ca. 425 ppm (2024), also um über 100 ppm in 64 Jahren. "
             "Der Anstieg ist im Vergleich 2000–2024 am stärksten (ca. 55 ppm in 24 Jahren "
             "gegenüber ca. 37 ppm in den ersten 30 Jahren)."),
        ],
    },
    "c0097": {
        "assets": {
            "abb1": {"source": ("undp_hdi", "vergleich")},
            "abb2": {"illustrative": True},
        },
        "edits": [
            ("t2", "answer_key",
             "b) Österreich hat HDI 0.926 – das entspricht einem sehr hohen Entwicklungsstand",
             "b) Österreich hat HDI 0,93 – das entspricht einem sehr hohen Entwicklungsstand"),
        ],
    },
}


def _find_block(content, block_id: str):
    for b in list(content.intro) + [b for s in content.sections for b in s.blocks]:
        if b.id == block_id:
            return b
    raise KeyError(f"block '{block_id}' not found")


def _find_section(content, section_id: str):
    for s in content.sections:
        if s.id == section_id:
            return s
    raise KeyError(f"section '{section_id}' not found")


def _replace(value, old: str, new: str) -> tuple[object, bool]:
    """Replace old→new in a str or in each element of a list[str]; report whether it hit."""
    if isinstance(value, str):
        return (value.replace(old, new), True) if old in value else (value, False)
    if isinstance(value, list):
        hit = False
        out = []
        for el in value:
            if isinstance(el, str) and old in el:
                out.append(el.replace(old, new)); hit = True
            else:
                out.append(el)
        return out, hit
    return value, False


def apply_plan(item_id: str, plan: dict) -> tuple[object, list[str]]:
    changes: list[str] = []
    store = ReviewStore()
    item = store.get(item_id)
    if item is None or item.content is None:
        raise KeyError(f"content item '{item_id}' not found in store")
    content = item.content

    for aid, ops in plan.get("assets", {}).items():
        asset = next((a for a in content.assets if a.id == aid), None)
        if asset is None:
            raise KeyError(f"{item_id}: asset '{aid}' not found")
        if "source" in ops:
            did, series = ops["source"]
            asset.data_source = DataRef(dataset_id=did, series=series)
            asset.illustrative = False
            changes.append(f"{aid}: data_source → {did}/{series}")
        if ops.get("illustrative"):
            asset.illustrative = True
            asset.data_source = None
            changes.append(f"{aid}: illustrative=True (schematisch)")
        if "title" in ops:
            asset.spec = {**(asset.spec or {}), "title": ops["title"]}
            changes.append(f"{aid}: title → {ops['title']!r}")

    for edit in plan.get("edits", []):
        if edit[0] == "@tp":
            _, sid, old, new = edit
            sec = _find_section(content, sid)
            tp = sec.teacher_overview.talking_points
            newtp, hit = _replace(tp, old, new)
            if not hit:
                raise ValueError(f"{item_id}: talking-point edit not matched in {sid}: {old[:50]!r}")
            sec.teacher_overview.talking_points = newtp
            changes.append(f"{sid}.talking_points: {old[:40]!r} → {new[:40]!r}")
        else:
            bid, field, old, new = edit
            b = _find_block(content, bid)
            cur = getattr(b, field, None)
            newval, hit = _replace(cur, old, new)
            if not hit:
                raise ValueError(f"{item_id}: text edit not matched in {bid}.{field}: {old[:50]!r}")
            setattr(b, field, newval)
            changes.append(f"{bid}.{field}: {old[:40]!r} → {new[:40]!r}")

    # re-run the real deterministic seam: assemble (grounds figures + stamps citations) → verify
    assemble(content, item.resolution)
    report = verify(content, item.resolution)
    item.content = content
    item.verify_problems = report.problems
    item.verify_warnings = report.warnings
    return item, changes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report only; do not save")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # the report prints → · umlauts
    except Exception:
        pass
    store = ReviewStore()
    for item_id, plan in PLAN.items():
        item, changes = apply_plan(item_id, plan)
        clabel = [w for w in item.verify_warnings if CLABEL in w]
        print(f"\n=== {item_id} ===")
        for c in changes:
            print(f"  · {c}")
        print(f"  (c)-label warnings after: {len(clabel)}  "
              f"| total warnings: {len(item.verify_warnings)} | problems: {len(item.verify_problems)}")
        for w in item.verify_warnings:
            print(f"     ! {w}")
        if item.verify_problems:
            for p in item.verify_problems:
                print(f"     X {p}")
        if not args.dry_run:
            store.save(item)
            print("  saved.")
    print("\nDone." + ("  (dry run — nothing saved)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
