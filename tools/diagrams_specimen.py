"""Specimen sheet for the DIAGRAM / bespoke recipe family after the figstyle port (A1).

cause_effect · process_flow (linear + cyclic) · em_spectrum · the truncated/honest axis pair
(intentionally-flawed vs its honest twin — the misleading one is drawn in the `negative` role and
its flaw is NEVER fixed) · math_formula. All on the semantic roles. LOOK and tune.

    python -m tools.diagrams_specimen [OUTDIR]     # default: runs/specimens/diagrams
"""
from __future__ import annotations

import sys
from pathlib import Path

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline.assets import build_asset
from teachersaid.schema.assets import Asset

CASES: dict[str, tuple[str, dict]] = {
    "cause_effect": ("matplotlib:cause_effect", {
        "links": [{"cause": "Industrialisierung", "effect": "Landflucht"},
                  {"cause": "Industrialisierung", "effect": "Wachstum der Städte"},
                  {"cause": "Landflucht", "effect": "Wohnungsnot"},
                  {"cause": "Wachstum der Städte", "effect": "Wohnungsnot"}],
        "title": "Wirkungsgefüge: Industrialisierung"}),
    "process_flow_linear": ("matplotlib:process_flow", {
        "steps": [{"name": "Beobachtung"}, {"name": "Fragestellung"}, {"name": "Hypothese"},
                  {"name": "Experiment"}, {"name": "Auswertung"}],
        "title": "Der naturwissenschaftliche Weg"}),
    "process_flow_cycle": ("matplotlib:process_flow", {
        "steps": [{"name": "Verdunstung"}, {"name": "Kondensation"}, {"name": "Niederschlag"},
                  {"name": "Abfluss"}, {"name": "Versickerung"}], "cyclic": True,
        "title": "Der Wasserkreislauf"}),
    "em_spectrum": ("matplotlib:em_spectrum", {}),
    "truncated_axis": ("matplotlib:truncated_axis", {
        "categories": ["Jän", "Feb", "Mär", "Apr"], "values": [102, 104, 107, 110],
        "ylabel": "Verkaufszahlen", "title": "Dramatischer Anstieg?!"}),
    "honest_axis": ("matplotlib:honest_axis", {
        "categories": ["Jän", "Feb", "Mär", "Apr"], "values": [102, 104, 107, 110],
        "ylabel": "Verkaufszahlen", "title": "Dieselben Daten, ehrliche Achse"}),
    "math_formula": ("matplotlib:math_formula", {
        "latex": r"a^2 + b^2 = c^2 \quad\Rightarrow\quad c = \sqrt{a^2 + b^2}"}),
}


def render(outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (gen, spec) in CASES.items():
        paths.append(build_asset(Asset(id=name, role="figure", generator=gen, spec=spec),
                                 outdir=outdir))
    return paths


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNS_DIR / "specimens" / "diagrams"
    for p in render(out):
        print(p)
