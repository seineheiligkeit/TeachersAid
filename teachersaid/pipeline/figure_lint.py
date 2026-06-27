"""The (c)-label gate (grounded-facts phase 1) — DETERMINISTIC, advisory.

The factual analogue of `media_policy.check_content` and `chart_lint`: every
content figure that presents empirical/statistical data must declare which kind of
claim it is — exactly one of
  * (b) **sourced** — `data_source` references a vetted dataset (the citation prints), or
  * (c) **illustrative** — `illustrative=True`, clearly schematic/example data.
A real-looking, *unlabelled* data figure is a verify warning (not blocking): it looks
verified but isn't. This is the honesty win the SME asked to formalize — the agents
already reach for "Schematisch" unprompted.

Pure-math figures (number_line, function_graph, math_formula) are abstract, not
"facts", so they're exempt; the same goes for a 0/1 classification (chart_lint owns it).
"""

from __future__ import annotations

from ..grounding.data_store import series_to_spec
from ..schema.worksheet import WorksheetContent

# generators that present empirical/statistical data (→ must declare provenance)
_DATA_GENERATORS = {
    "matplotlib:bar_chart", "matplotlib:line", "matplotlib:scatter",
    "matplotlib:histogram", "matplotlib:population_pyramid",
    "matplotlib:timeline", "matplotlib:climate_diagram",
}


def _has_real_numbers(spec: dict) -> bool:
    vals: list[float] = []
    for key in ("values", "male", "female", "temp", "precip"):
        vals += [float(v) for v in (spec.get(key) or []) if v not in (None, "")]
    for ser in spec.get("series") or []:
        vals += [float(v) for v in (ser.get("y") or []) if v not in (None, "")]
    for p in spec.get("points") or []:
        if len(p) >= 2:
            vals.append(float(p[1]))
    for e in spec.get("events") or []:        # a timeline's dates are facts too
        if e.get("at") not in (None, ""):
            vals.append(float(e["at"]))
    if not vals:
        return False
    return set(vals) != {0.0, 1.0}          # a 0/1 classification is chart_lint's job


def lint_content(content: WorksheetContent) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    for a in getattr(content, "assets", []):
        if (a.generator or "") not in _DATA_GENERATORS:
            continue
        if a.data_source is not None:
            # (b) — verify the dataset/series resolves AND maps to real values
            _, ns = series_to_spec(a.data_source, a.generator or "")
            warnings += [f"asset '{a.id}': {n}" for n in ns]
            continue
        if a.illustrative:
            continue                                 # (c) — declared schematic
        if _has_real_numbers(a.spec or {}):
            warnings.append(
                f"asset '{a.id}': Zahlen ohne Quellenangabe — als echte Daten "
                f"data_source (zitierter Datensatz) setzen, sonst illustrative=true "
                f"(schematisch). Unbelegte echte Zahlen wirken geprüft, sind es aber nicht.")
    return problems, warnings
