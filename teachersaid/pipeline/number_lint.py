"""Numeric-claims lint (Track 1 #2, offline-first program) — DETERMINISTIC, advisory.

`ground_data` derives a FIGURE's values from its cited dataset slice — but a task's
prose (prompt / answer_key / acceptable_reasoning) can still carry authored numbers
right next to that figure (found in the 2 Jul 2026 review: a Bevölkerungspyramide
worksheet whose answer key stated population counts nothing ever checked). This lint
closes that last authored-number hole: every substantial number in a task that
references a **sourced** data figure must be *derivable from the cited dataset
slice* — the entity-lint pattern (sachverhalt_lint: every prose year ∈ fact-set)
applied to numbers-vs-dataset. Under the offline-first pivot it doubles as the
anti-rot mechanism: derived values re-ground on dataset refresh, while an authored
number that no longer derives shows up here instead of going silently stale.

"Derivable" = matches, at the precision the prose claims, a member of a bounded
closure of the slice's values: the values themselves · contiguous-range sums
(75+ = 75–79 + 80–84 + 85+) · elementwise cross-series sums (male+female) ·
same-range cross-series differences ("um 129.000 mehr Frauen") · shares of a total
in percent. A claim rounded to N significant digits is checked as that rounding —
"ca. 129.000" matches 129 086; "über 600.000" (1 significant digit) is deliberately
coarse and matches coarsely.

False-positive discipline (the sachverhalt-lint lesson — there: years hard, names
advisory; here: value claims checked, calendar left alone):
* skipped — bare numbers < MIN_CHECK (didactic counts, "2–3 Sätze", Zeilennummern),
  unformatted 4-digit calendar years 1200–2100 (birth-cohort arithmetic is not in
  the slice; years stay the Sachverhalt lint's domain), and numbers that exactly
  match a slice label (age-band edges, event years, categories);
* checked — absolute claims ≥ MIN_CHECK and every %-claim;
* advisory (warning lane) — the SME gate stays the judge (invariants §7/§10).

Runs in `verify` next to `figure_lint`; resolves the dataset directly via
`series_to_spec`, so it does not depend on `ground_data` having run first.
"""

from __future__ import annotations

import math
import re
from itertools import combinations

from ..grounding.data_store import get_dataset
from ..schema.enums import Role
from ..schema.worksheet import WorksheetContent
from .figure_lint import _DATA_GENERATORS

# Below this a bare absolute number reads as a didactic count, an age, a Zeilennummer
# or an axis mention ("über 85", "Nenne 3 Gruppen"), not a data claim. Percent claims
# are always checked. Calibrated on the staged GWB data pass (2 Jul 2026).
MIN_CHECK = 120.0
_YEAR_RANGE = (1200, 2100)  # unformatted integers here read as calendar years → skipped
_MAX_POOL = 60_000          # defensive cap on the derivation closure
_MAX_WARN_PER_TASK = 4      # keep the warning lane readable

# a grouped number is never directly followed by another digit — that would be a
# date fragment ("1.1.2024" must not tokenize as 1.202); dates are stripped first.
# Thousands separators: dot (9.158.750) or (narrow no-break) space (104 080).
_DATE = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")
_NUM = re.compile(r"\d{1,3}(?:[.   ]\d{3})+(?:,\d+)?(?!\d)|\d+(?:,\d+)?")
_PCT_AFTER = re.compile(r"^\s*(?:%|Prozent)")
_MULT_AFTER = re.compile(r"^\s*(Millionen|Million|Mio\.?|Milliarden|Milliarde|Mrd\.?|Tausend)\b",
                         re.IGNORECASE)
_MULT = {"million": 1e6, "millionen": 1e6, "mio": 1e6, "mio.": 1e6,
         "milliarde": 1e9, "milliarden": 1e9, "mrd": 1e9, "mrd.": 1e9, "tausend": 1e3}


# --- claim extraction (German number formats) ---------------------------------

def _flat(rt) -> str:
    """RichText (str | list[InlineRun] | None) → plain text."""
    if rt is None:
        return ""
    if isinstance(rt, str):
        return rt
    if isinstance(rt, list):
        return "".join(getattr(r, "text", "") or "" for r in rt)
    return str(rt)


def _claims(text: str) -> list[tuple[float, bool, int, str]]:
    """(value, is_percent, significant_digits, raw) for each numeric token.
    Handles dot-grouped thousands (9.158.750), comma decimals (21,2), a trailing
    %/Prozent, and Mio./Milliarden/Tausend multipliers. Trailing zeros of a plain
    integer are treated as NOT significant (a rounded prose claim like "129.000"),
    which widens the matching tolerance accordingly."""
    out: list[tuple[float, bool, int, str]] = []
    for m in _NUM.finditer(_DATE.sub(" ", text or "")):
        raw = m.group(0)
        intpart, _, dec = raw.partition(",")
        digits = re.sub(r"[.   ]", "", intpart)
        try:
            val = float(digits) + (float(f"0.{dec}") if dec else 0.0)
        except ValueError:              # pragma: no cover — regex guarantees digits
            continue
        tail = text[m.end():]
        is_pct = bool(_PCT_AFTER.match(tail))
        mm = _MULT_AFTER.match(tail)
        if mm and not is_pct:
            val *= _MULT[mm.group(1).casefold()]
        if dec:
            sig = len(digits.lstrip("0") or "0") + len(dec)
        else:
            sig = len((digits.lstrip("0") or "0").rstrip("0") or "0")
        out.append((val, is_pct, max(sig, 1), raw))
    return out


def _matches(claim: float, sig: int, pool) -> bool:
    """True if some derivable value rounds to the claim at its stated precision."""
    if claim == 0:
        return True
    tol = 0.5 * 10 ** (math.floor(math.log10(abs(claim))) - (sig - 1))
    return any(abs(u - claim) <= tol + 1e-9 for u in pool)


# --- the derivation closure of a dataset slice ---------------------------------
# The universe derives from the FULL cited series, not from the chart's projection
# of it: a series may carry counts AND shares_pct — the figure shows one column,
# but the prose may legitimately quote the other (calibration finding, 2 Jul 2026).

_LABEL_KEYS = frozenset((
    "groups", "categories", "age_groups", "months", "labels", "years", "x",
))


def _arrays(series: dict) -> list[list[float]]:
    arrs: list[list[float]] = []
    for key, v in (series or {}).items():
        if key in _LABEL_KEYS:
            continue                                  # axis labels are not data values
        if isinstance(v, list) and v:
            if all(isinstance(x, (int, float)) for x in v):
                arrs.append([float(x) for x in v])
            elif all(isinstance(x, dict) for x in v):  # multi-series: [{label, y: […]}]
                for ser in v:
                    ys = ser.get("y")
                    if isinstance(ys, list):
                        nums = [float(x) for x in ys if isinstance(x, (int, float))]
                        if nums:
                            arrs.append(nums)
        elif isinstance(v, dict):                     # choropleth-style {region: value}
            nums = [float(x) for x in v.values() if isinstance(x, (int, float))]
            if nums:
                arrs.append(nums)
    return [a for a in arrs if a]


def _contig_sums(a: list[float]) -> list[float]:
    out: list[float] = []
    for i in range(len(a)):
        s = 0.0
        for j in range(i, len(a)):
            s += a[j]
            out.append(s)
    return out


def _contig_stats(a: list[float]) -> list[float]:
    """Means of contiguous ranges + pairwise midpoints — the Mittelwert/Median
    derivations a MAT statistics task legitimately states about the slice."""
    out: list[float] = []
    for i in range(len(a)):
        s = 0.0
        for j in range(i, len(a)):
            s += a[j]
            out.append(s / (j - i + 1))
    if len(a) <= 60:
        out += [(x + y) / 2 for x, y in combinations(a, 2)]   # median of an even count
    return out


def _label_numbers(series: dict) -> set[float]:
    """Numbers that appear as labels of the slice (band edges, categories, event
    years) — exempt: mentioning an axis label is not a data claim."""
    out: set[float] = set()
    for key in _LABEL_KEYS:
        for lab in (series.get(key) or []):
            if isinstance(lab, (int, float)):
                out.add(float(lab))
            else:
                for v, _pct, _sig, _raw in _claims(str(lab)):
                    out.add(v)
    for v in (series.get("values") or {}) if isinstance(series.get("values"), dict) else []:
        for n, _pct, _sig, _raw in _claims(str(v)):
            out.add(n)
    for e in series.get("events") or []:
        at = e.get("at") if isinstance(e, dict) else None
        if isinstance(at, (int, float)):
            out.add(float(at))
    return out


def build_universe(series: dict) -> tuple[list[float], list[float]]:
    """(absolute pool, percent pool) derivable from a cited series."""
    arrays = _arrays(series)
    agg: list[float] = []
    for a in arrays:
        agg += _contig_sums(a)
    for a, b in combinations(arrays, 2):             # male+female per band, etc.
        if len(a) == len(b):
            agg += _contig_sums([x + y for x, y in zip(a, b)])
    totals = {sum(a) for a in arrays}
    totals |= {sum(a) + sum(b) for a, b in combinations(arrays, 2) if len(a) == len(b)}
    diffs: list[float] = []
    for a, b in combinations(arrays, 2):             # same-range cross-series gaps
        if len(a) == len(b):
            ca, cb = _contig_sums(a), _contig_sums(b)
            diffs += [abs(x - y) for x, y in zip(ca, cb)]
    stats: list[float] = []
    for a in arrays:
        stats += _contig_stats(a)
    pool = (agg + sorted(totals) + diffs + stats)[:_MAX_POOL]
    pcts: list[float] = []
    for t in totals:
        if t:
            pcts += [100.0 * v / t for v in agg]
    pcts += [100.0 - p for p in list(pcts)]
    # within-array ratios ("die Schweiz liegt bei rund 180 % des österreichischen Werts")
    for a in arrays:
        if len(a) <= 60:
            pcts += [100.0 * x / y for x in a for y in a if y]
    return pool, pcts[:_MAX_POOL]


# --- the lint -------------------------------------------------------------------

def lint_content(content: WorksheetContent) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    warnings: list[str] = []

    universes: dict[str, tuple[list[float], list[float], set[float], object]] = {}
    for a in getattr(content, "assets", []):
        if (a.generator or "") not in _DATA_GENERATORS or a.data_source is None:
            continue
        ds = get_dataset(a.data_source.dataset_id)
        series = ds.series.get(a.data_source.series) if (ds and a.data_source.series) else None
        if not isinstance(series, dict):
            continue                    # resolution gaps are figure_lint's warnings
        pool, pcts = build_universe(series)
        if not pool:
            continue
        universes[a.id] = (pool, pcts, _label_numbers(series), a.data_source)
    if not universes:
        return problems, warnings

    for b in content.iter_blocks():
        if b.role != Role.TASK:
            continue
        srcs = [universes[r] for r in (getattr(b, "asset_refs", None) or []) if r in universes]
        if not srcs:
            continue
        text = " ".join(
            _flat(t) for t in (b.prompt, b.answer_key, b.acceptable_reasoning) if t is not None
        )
        flagged = 0
        for val, is_pct, sig, raw in _claims(text):
            if not is_pct:
                if val < MIN_CHECK:
                    continue
                if (_YEAR_RANGE[0] <= val <= _YEAR_RANGE[1] and val.is_integer()
                        and "." not in raw and "," not in raw):
                    continue            # an unformatted 4-digit integer reads as a year
            if any(any(abs(val - lab) < 1e-9 for lab in labels) for _p, _q, labels, _d in srcs):
                continue                # slice label (band edge, category, event year)
            # a %-claim may also cite a value that IS a percentage in the dataset
            # (urbanisation shares etc.), so it checks both pools
            ok = any(_matches(val, sig, (pool + pcts if is_pct else pool))
                     for pool, pcts, _labels, _ref in srcs)
            if not ok:
                flagged += 1
                if flagged <= _MAX_WARN_PER_TASK:
                    ref = srcs[0][3]
                    warnings.append(
                        f"{b.id}: Zahl „{raw}{' %' if is_pct else ''}“ ist aus dem zitierten "
                        f"Datensatz ({ref.dataset_id}/{ref.series}) nicht ableitbar — "
                        f"Wert prüfen oder aus den Daten ableiten"
                    )
        if flagged > _MAX_WARN_PER_TASK:
            warnings.append(f"{b.id}: … + {flagged - _MAX_WARN_PER_TASK} weitere nicht "
                            f"ableitbare Zahlen")
    return problems, warnings
