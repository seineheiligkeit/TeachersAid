"""Chart representation sanity (Phase: review pass) — DETERMINISTIC, advisory.

Correct data is necessary but NOT sufficient: the chart *type* and *scale* must make
the data legible and meaningful. The recipes auto-fix legibility (label overlap, value
labels, layout); this linter flags the harder, semantic misuses a recipe can't fix
itself, as `verify` warnings the reviewer (and the AI) see:

* a bar chart of only 0/1 values is a classification, not a quantity comparison
  (a bar chart misrepresents it — and such charts often leak the answer);
* values spanning many orders of magnitude on a linear bar chart — the recipe's value
  labels keep them readable, but it's worth a human deciding whether linear (emphasise
  the size difference) or log/`spec.log` (emphasise orders of magnitude) tells the right
  story.
"""
from __future__ import annotations

import re

# the recipe value-labels small bars, so a wide range is a representation *judgment*,
# not a legibility bug — only flag genuinely extreme spreads for that judgment.
_WIDE_RANGE = 100
_MONTHS = {"jän", "jan", "feb", "mär", "mar", "apr", "mai", "jun", "jul",
           "aug", "sep", "okt", "nov", "dez"}


def _looks_numeric(cats: list[str]) -> bool:
    return bool(cats) and all(re.fullmatch(r"-?\d+([.,]\d+)?\*?", c.strip()) for c in cats)


def _looks_temporal(cats: list[str]) -> bool:
    if not cats:
        return False
    years = all(re.fullmatch(r"(18|19|20)\d\d\*?", c.strip()) for c in cats)
    months = all(c.strip().lower()[:3] in _MONTHS for c in cats)
    return years or months


def lint_content(content) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []
    for a in getattr(content, "assets", []):
        if a.generator != "matplotlib:bar_chart":
            continue
        vals = [float(v) for v in (a.spec.get("values") or []) if v not in (None, "")]
        nz = [abs(v) for v in vals if v]
        cats = [str(c) for c in (a.spec.get("values") and a.spec.get("categories") or [])]
        if len(vals) >= 3 and set(vals) <= {0.0, 1.0}:
            warnings.append(
                f"asset '{a.id}': Balkendiagramm aus nur 0/1 — das ist eine Klassifikation, "
                f"kein Mengenvergleich (als Balken ungeeignet; verrät oft die Lösung)")
        elif _looks_temporal(cats):           # years are numeric too → check temporal first
            warnings.append(
                f"asset '{a.id}': Zeitreihe (Jahre/Monate) als Balken — ein Liniendiagramm "
                f"(intent trend) zeigt den Verlauf besser")
        elif _looks_numeric(cats):
            warnings.append(
                f"asset '{a.id}': numerische x-Werte als Balken-Kategorien — das ist ein "
                f"Zusammenhang/Verlauf; ein Streu- oder Liniendiagramm (intent relationship/trend) "
                f"passt besser als Balken")
        elif nz and max(nz) / min(nz) > _WIDE_RANGE and not a.spec.get("log"):
            warnings.append(
                f"asset '{a.id}': Werte spannen {max(nz) / min(nz):.0f}× — prüfen, ob linear "
                f"(Größenunterschied betonen) oder log-Skala (spec.log; Größenordnungen) die "
                f"richtige Darstellung ist")
    return problems, warnings
