"""Difficulty as a COMPUTED, ADVISORY quantity (roadmap C4).

`pipeline/difficulty.py` gives every task an *effective* difficulty (the author/SME
`difficulty` 1–3 if set, else the Anforderungsbereich of its `cognitive_level`). This
module adds a **second, independent opinion**: a transparent estimate derived from the
task's own surface features, used ONLY to flag a task for SME review when it disagrees
with the operative difficulty by ≥1 band. It NEVER overrides the authored value — the
discipline of C4 is DERIVED + ADVISORY (see CLAUDE.md's lint-lane rule, `verify.py`).

## The load-bearing honesty (read `Documents/difficulty-model.md` for the full study)

The block corpus (`store/blockstore.py`) carries **zero** authored `difficulty` labels —
all ~1000 task blocks fall back to the cognitive-level band. So the only "label" available
to fit against is itself a deterministic function of ONE feature (`cognitive_level`). An
unconstrained accuracy-maximising fit therefore trivially recovers `cognitive_rank`
(100 % exact, 0 disagreements, every other weight driven to zero) — a mathematically exact
but epistemically vacuous fit, and a MUTE advisory. A difficulty model is, in the strict
sense, **not learnable** from this corpus.

The design response is **anchor-and-nudge**, and it is deliberately NOT a pure fit:
* the **cognitive level is the anchor** (a strong prior — it *is* the operative difficulty
  signal the corpus already encodes), carried by a dominant curated weight;
* the **intrinsic surface features** (text load, kind cost, number domain, answer-surface
  openness, and — for parametric blocks — solution-step count and math depth) are an
  INDEPENDENT nudge with modest curated weights;
* when the nudge is strong enough to push the estimate across a band boundary, that ≥1-band
  disagreement is the **review cue**. The signal that fires the warning is the intrinsic
  features, not the anchor — so it is not circular.

Only the **two thresholds** are fit to the corpus (deterministic grid search, see
`tools/fit_difficulty.py`); the weights are curated with a documented didactic rationale
(every weight is POSITIVE — each feature makes a task harder as it grows — a sign the SME
can sanity-check). On the corpus this yields 95.4 % exact / 100 % adjacent agreement with
the cognitive band and flags ≈4.6 % of blocks — a focused, balanced review list. 100 %
adjacent means the estimate never disagrees by two bands: appropriate for an advisory.

Persisted model: `pipeline/difficulty_weights.json` (versioned, reviewable — not a pickle).
FUTURE seam (documented, NOT depended upon): a prerequisite-graph depth feature once the
Wave-C1 concept graph exists — see the design doc.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..schema.enums import COGNITIVE_RANK, Role
from ..schema.richtext import InlineRun
from .readability import extract_prose, wstf

# --- feature order (the weighted-sum vector; JSON + weights key on these names) ----------
FEATURE_NAMES = ("steps", "math", "numdom", "text", "kind", "open", "cog")

# German feature labels for the advisory review-cue wording (verify.py / Einblicke digest).
FEATURE_LABELS_DE = {
    "steps": "Lösungsschritte", "math": "Rechenausdruck-Tiefe", "numdom": "Zahlenbereich",
    "text": "Textlast", "kind": "Aufgabentyp", "open": "offenes Antwortformat",
    "cog": "kognitive Stufe",
}

# --- curated weights (the CANONICAL source; the fit tool copies these into the JSON) -----
# All POSITIVE (each feature makes a task harder as it grows — the sign an SME sanity-checks).
# `cog` is the dominant ANCHOR (the operative difficulty prior); the rest are bounded nudges.
# These are NOT machine-learned (they cannot be — see the module docstring); only the two
# thresholds are fit. `tools/fit_difficulty.py` writes {these weights, fitted thresholds} to
# difficulty_weights.json; `tests/test_difficulty_model.py` locks JSON == CURATED_WEIGHTS.
CURATED_WEIGHTS: dict[str, float] = {
    "cog": 3.0,     # ANCHOR — the cognitive-level band, the corpus's operative difficulty
    "kind": 0.70,   # inherent demand of the task genre
    "text": 0.50,   # prose reading load (WSTF)
    "steps": 0.60,  # derived Rechenweg length (parametric blocks)
    "math": 0.60,   # math-expression depth (parametric blocks)
    "numdom": 0.40,  # number domain ℕ→ℤ→fractions→irrational
    "open": 0.30,   # answer-surface openness (free response > closed choices)
}

# --- normalization caps (each raw feature → [0,1]) --------------------------------------
STEP_CAP = 6      # a Rechenweg of ≥6 steps saturates the step-count feature
MATH_CAP = 8      # ≥8 counted operations saturates the math-depth feature
WSTF_FLOOR = 4.0  # WSTF Schulstufe mapped to text-load 0.0 (very easy)
WSTF_CEIL = 14.0  # WSTF Schulstufe mapped to text-load 1.0 (academic)
TEXT_NEUTRAL = 0.4  # text-load for a prompt too short to score (< MIN_WORDS_FOR_ESTIMATE)

# --- the answer-surface "openness" ladder ------------------------------------------------
# More openness → harder (a blank page demands more than picking an option). Aligned with
# the renderer's `_SELF_CONTAINED_PAYLOADS` (ordering/matching/multiple_choice/role_play):
# those give a CLOSED answer set. `table_fill`/`table` scaffolds generation into a grid
# (half-open). Everything else (open_response, true_false_justify — its justification needs
# lines — decision_scenario, …) is a free written response (open).
_SELF_CONTAINED = {"ordering", "matching", "multiple_choice", "role_play"}

# --- kind base-cost (curated, didactic; the inherent demand of the task GENRE) -----------
# Three tiers. Derived from the KIND, not the assigned cognitive_level, so it is a partly
# independent signal (a multiple_choice can probe analysis; an open_response can probe
# recall). SME-tunable; the exact bin of a borderline genre barely moves the estimate (one
# feature among several, weight 0.7). Unlisted kinds default to the middle tier.
_KIND_LOW = frozenset({  # recognition / structured recall / closed drill
    "matching", "ordering", "multiple_choice", "true_false_justify", "table_fill",
    "reading_task", "listening_task", "content_comprehension", "structure_overview",
    "cause_effect_match", "map_work", "training_log", "puzzle",
})
_KIND_HIGH = frozenset({  # analyse / evaluate / produce / argue / design / model
    "create_produce", "make_artifact", "text_production", "writing_task", "design_task",
    "position_argument", "argumentation", "eroerterung", "dilemma", "decision_scenario",
    "case_study", "source_analysis", "source_critique", "text_analysis", "textanalyse",
    "dekonstruktion", "data_analysis",
})
KIND_COST_LOW, KIND_COST_MID, KIND_COST_HIGH = 0.25, 0.55, 0.80


def _kind_cost(kind: str) -> float:
    if kind in _KIND_LOW:
        return KIND_COST_LOW
    if kind in _KIND_HIGH:
        return KIND_COST_HIGH
    return KIND_COST_MID  # open_response, calculation, data_interpretation, translation, …


# --- number-domain class: ℕ < ℤ < fractions/decimals < irrational ------------------------
_IRRATIONAL = re.compile(r"[√π∛]|\\sqrt|\\pi\b|\bWurzel\b|\birrational")
_FRACTIONAL = re.compile(r"\d+[.,]\d+|\d+\s*/\s*\d+|\\frac|[½¼¾⅓⅔⅛]|%|\bProzent\b|\bBruch\b|\bBrüche\b")
_NEGATIVE = re.compile(r"(?<![\w–-])-\s?\d|\bminus\b|\bnegativ")


def _number_domain(text: str) -> int:
    """Highest number-domain marker present: 0 ℕ/none · 1 ℤ · 2 fractions/decimals · 3
    irrational. Advisory-lane (like readability): the negative-integer probe is deliberately
    conservative (a hyphen or a `1–5` range must not read as ℤ), so a bare negative in prose
    can be missed — an accepted, documented miss on a modestly-weighted feature."""
    if _IRRATIONAL.search(text):
        return 3
    if _FRACTIONAL.search(text):
        return 2
    if _NEGATIVE.search(text):
        return 1
    return 0


# --- math depth: sympy where possible, else a token count --------------------------------
_LATEX_OPS = re.compile(
    r"\\frac|\\sqrt|\\cdot|\\times|\\div|\\int|\\sum|\\prod|\\lim|\\log|\\ln|"
    r"\\sin|\\cos|\\tan|\\leq|\\geq|\\neq|\\pm|[+\-*/^=<>]"
)


def _latex_cleanup(frag: str) -> str:
    """Best-effort LaTeX → sympifiable text (enough for a count_ops proxy, not a faithful
    parse). Unhandled constructs make sympify fail → the regex fallback takes over."""
    s = frag
    s = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"((\1)/(\2))", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)", s)
    s = s.replace("\\cdot", "*").replace("\\times", "*").replace("\\div", "/")
    s = s.replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\\[,;: ]", " ", s)          # thin spaces
    s = re.sub(r"\\(leq|geq|neq)\b", "=", s)  # comparisons → an equality op (depth proxy)
    s = s.replace("^", "**")
    s = re.sub(r"\\[a-zA-Z]+", " ", s)        # drop any remaining macros
    return s


def _math_ops(frag: str) -> int:
    """Operation count for one math fragment. Tries sympy (`count_ops`) on a cleaned form;
    on any failure falls back to counting operator tokens in the raw LaTeX."""
    cleaned = _latex_cleanup(frag)
    # split an equation into sides so `=` doesn't defeat sympify; sum the parts' ops (+1
    # per relation for the comparison itself)
    try:
        from sympy.parsing.sympy_parser import (
            implicit_multiplication_application, parse_expr, standard_transformations,
        )
        tr = standard_transformations + (implicit_multiplication_application,)
        pieces = re.split(r"[=<>]", cleaned)
        rels = max(len(pieces) - 1, 0)
        total = rels
        parsed_any = False
        for p in pieces:
            p = p.strip()
            if not p:
                continue
            expr = parse_expr(p, transformations=tr, evaluate=False)
            total += int(expr.count_ops())
            parsed_any = True
        if parsed_any:
            return total
    except Exception:
        pass
    return len(_LATEX_OPS.findall(frag))


def _math_fragments(prompt) -> list[str]:
    """Every math fragment in a prompt: math-flagged inline runs (the canonical parametric
    case — `$…$` template spans become math runs) plus any `$…$` in plain text (robustness)."""
    frags: list[str] = []
    plain_parts: list[str] = []
    if isinstance(prompt, str):
        plain_parts.append(prompt)
    elif isinstance(prompt, list):
        for r in prompt:
            if isinstance(r, InlineRun):
                (frags if r.math else plain_parts).append(r.text)
            elif isinstance(r, dict):
                (frags if r.get("math") else plain_parts).append(r.get("text", ""))
    for txt in plain_parts:
        frags += re.findall(r"\$([^$]+)\$", txt)
    return [f for f in frags if f.strip()]


# --- the feature vector ------------------------------------------------------------------

def _prompt_of(block) -> object:
    return getattr(block, "prompt", None)


def features(block) -> dict[str, float] | None:
    """The transparent, documented, task-only feature vector, each value in [0,1].

    Returns None for anything that isn't a task block (difficulty is a task property).
    Every value is reproducible and cheap — derivable from the block alone:

      steps  len(solution_steps)/STEP_CAP        — the derived Rechenweg length (parametric)
      math   counted math operations/MATH_CAP    — sympy count_ops over `$…$`, else tokens
      numdom number-domain class / 3             — ℕ<ℤ<fractions/decimals<irrational
      text   WSTF Schulstufe, floor..ceil → 0..1 — prose load of the prompt (math excluded)
      kind   curated kind base-cost              — inherent demand of the task genre
      open   answer-surface openness (0/.5/1)    — closed choices → half-open grid → free
      cog    cognitive_rank / 5                  — the ANCHOR (see module docstring)

    `steps` and `math` are structurally 0 for every harvested library block (those are
    prose worksheet tasks, not parametric) — they carry signal only for parametric blocks
    (MAT/CHE/PHY variant packs). This is documented, not a bug (see `difficulty-model.md`).
    """
    if getattr(block, "role", None) != Role.TASK:
        return None
    prompt = _prompt_of(block)
    prose = extract_prose(prompt)            # math runs already excluded by readability
    w = wstf(prose)
    text_load = TEXT_NEUTRAL if w is None else max(
        0.0, min(1.0, (w - WSTF_FLOOR) / (WSTF_CEIL - WSTF_FLOOR)))

    ops = max((_math_ops(f) for f in _math_fragments(prompt)), default=0)

    pk = getattr(getattr(block, "payload", None), "kind", None)
    rm = getattr(getattr(block, "response", None), "mode", None)
    if pk in _SELF_CONTAINED or rm == "choices":
        openness = 0.0
    elif pk == "table_fill" or rm == "table":
        openness = 0.5
    else:
        openness = 1.0

    return {
        "steps": min(len(getattr(block, "solution_steps", []) or []) / STEP_CAP, 1.0),
        "math": min(ops / MATH_CAP, 1.0),
        "numdom": _number_domain(prose) / 3.0,
        "text": text_load,
        "kind": _kind_cost(getattr(block, "kind", "")),
        "open": openness,
        "cog": COGNITIVE_RANK.get(getattr(block, "cognitive_level", ""), 1) / 5.0,
    }


# --- the fitted model --------------------------------------------------------------------

class DifficultyEstimate(BaseModel):
    """One block's computed second opinion. `contributions` = weight·feature per feature,
    so the SME sees exactly what drove the estimate (transparency is the point)."""
    model_config = ConfigDict(extra="forbid")
    band: int                       # 1 · 2 · 3
    score: float                    # the weighted sum
    features: dict[str, float] = Field(default_factory=dict)
    contributions: dict[str, float] = Field(default_factory=dict)


_WEIGHTS_PATH = Path(__file__).with_name("difficulty_weights.json")


@lru_cache(maxsize=1)
def _load_model() -> dict:
    """Load {version, weights, thresholds, …} from the persisted JSON (cached). This is the
    single runtime source of truth for weights AND thresholds — the reviewable data file."""
    with _WEIGHTS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def band_for_score(score: float, thresholds: tuple[float, float]) -> int:
    t1, t2 = thresholds
    return 1 if score < t1 else 2 if score < t2 else 3


def top_drivers(est: DifficultyEstimate, k: int = 2) -> list[str]:
    """The k intrinsic features (excluding the `cog` anchor) carrying the most weight in this
    estimate — the 'maßgebliche Merkmale' the advisory names for the SME. May be shorter than
    k (or empty) when a task's intrinsic signals are all near zero."""
    intrinsic = sorted(
        ((n, c) for n, c in est.contributions.items() if n != "cog"),
        key=lambda nc: nc[1], reverse=True)
    return [FEATURE_LABELS_DE[n] for n, c in intrinsic[:k] if c > 0]


def estimate(block) -> DifficultyEstimate | None:
    """The computed difficulty band (1–3) + the contributing features for one task block,
    or None for a non-task block. ADVISORY only — never writes back onto the block."""
    feats = features(block)
    if feats is None:
        return None
    model = _load_model()
    weights = model["weights"]
    t1, t2 = model["thresholds"]
    contrib = {k: round(weights.get(k, 0.0) * feats[k], 4) for k in FEATURE_NAMES}
    score = sum(contrib.values())
    return DifficultyEstimate(
        band=band_for_score(score, (t1, t2)),
        score=round(score, 4),
        features={k: round(feats[k], 4) for k in FEATURE_NAMES},
        contributions=contrib,
    )
