"""Roadmap C4 — difficulty as a COMPUTED, ADVISORY quantity.

Covers: the transparent feature vector on fixture blocks (each feature's ground truth); the
math-depth feature's sympy path AND its regex fallback; the shipped weights JSON round-trip
(weights == the canonical curated dict, thresholds, feature order); estimate() determinism +
bounds; the fit's determinism/consistency against the corpus; and — the load-bearing
discipline — the verify advisory FIRING on a planted disagreement while NEVER mutating the
authored `difficulty` (it is a review cue, not a correction).
"""

from __future__ import annotations

import json
from datetime import date

from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline import difficulty_model as dm
from teachersaid.pipeline.resolve import resolve_kompetenzbereich
from teachersaid.pipeline.verify import verify
from teachersaid.schema.blocks import MatchingPayload, Serves, TaskBlock
from teachersaid.schema.response import ChoicesResponse, LinesResponse, TableResponse
from teachersaid.schema.richtext import InlineRun
from teachersaid.schema.worksheet import Baustein, WorksheetContent, WorksheetMeta

IN = date(2026, 3, 1)
PHY = "Physik"
PHY_KB = "Strahlung und Radioaktivität"


def _task(bid="t", *, kind="open_response", prompt="Aufgabe.", level="apply",
          difficulty=None, response=None, payload=None, solution_steps=None):
    return TaskBlock(
        id=bid, kind=kind, prompt=prompt, payload=payload,
        response=response or LinesResponse(n=2), cognitive_level=level,
        difficulty=difficulty, dimensions=["S"], est_minutes=10,
        solution_steps=solution_steps or [],
        serves=[Serves(competence_id="PHY.US.4.STR.02", relation="exercises")])


# --- 1) feature ground truths ------------------------------------------------------------

def test_features_none_for_info_block():
    from teachersaid.schema.blocks import InfoBlock
    assert dm.features(InfoBlock(id="i", kind="prose", content="Text.")) is None


def test_feature_vector_ground_truth():
    # short prompt (< MIN_WORDS) → text = TEXT_NEUTRAL; open_response → open=1.0; apply → cog 0.4
    f = dm.features(_task(kind="open_response", level="apply"))
    assert f == {
        "steps": 0.0, "math": 0.0, "numdom": 0.0, "text": dm.TEXT_NEUTRAL,
        "kind": dm.KIND_COST_MID, "open": 1.0, "cog": 2 / 5,
    }


def test_number_domain_ladder():
    nd = dm._number_domain
    assert nd("Zähle die Äpfel: 3 und 4.") == 0                 # ℕ / bare digits
    assert nd("Die Temperatur ist -5 Grad kalt.") == 1          # ℤ (negative)
    assert nd("Kürze den Bruch 3/4 so weit wie möglich.") == 2  # fractions
    assert nd("Berechne die Wurzel aus 2 näherungsweise.") == 3  # irrational marker
    # a hyphenated range / word-hyphen must NOT read as a negative integer (conservative)
    assert nd("Lies die Zeilen 3-4 im Text.") == 0


def test_kind_cost_tiers():
    assert dm._kind_cost("matching") == dm.KIND_COST_LOW
    assert dm._kind_cost("open_response") == dm.KIND_COST_MID
    assert dm._kind_cost("create_produce") == dm.KIND_COST_HIGH
    assert dm._kind_cost("some_unlisted_kind") == dm.KIND_COST_MID  # default = middle tier


def test_openness_ladder():
    # self-contained payload (matching) → closed answer surface
    assert dm.features(_task(kind="matching", payload=MatchingPayload(left=["a"], right=["b"])))["open"] == 0.0
    # choices response → closed
    assert dm.features(_task(response=ChoicesResponse(options=["a", "b"], select="one")))["open"] == 0.0
    # table response → half-open (generation into a grid)
    assert dm.features(_task(response=TableResponse(columns=["x"], rows=2)))["open"] == 0.5
    # free written response → open
    assert dm.features(_task(response=LinesResponse(n=3)))["open"] == 1.0


def test_solution_steps_feature_lives_for_parametric():
    from teachersaid.schema.blocks import SolutionStep
    steps = [SolutionStep(text=f"Schritt {i}") for i in range(3)]
    assert dm.features(_task(solution_steps=steps))["steps"] == 3 / dm.STEP_CAP
    # saturates at the cap
    many = [SolutionStep(text="s") for _ in range(20)]
    assert dm.features(_task(solution_steps=many))["steps"] == 1.0


def test_math_depth_sympy_path_and_regex_fallback():
    # sympy path: a clean expression parses → count_ops > 0
    assert dm._math_ops("x^2 + 3x + 2") > 0
    # regex fallback: an un-parseable fragment still counts operator tokens
    assert dm._math_ops("5 +") == 1              # only the '+' token; sympy raises → fallback
    # a math-flagged inline run feeds the feature
    prompt = [InlineRun(text="Berechne "), InlineRun(text="x^2 + 2x", math=True)]
    assert dm.features(_task(prompt=prompt))["math"] > 0
    # no math anywhere → 0
    assert dm.features(_task(prompt="Erkläre das Phänomen."))["math"] == 0.0


# --- 2) the persisted model round-trips --------------------------------------------------

def test_shipped_weights_json_roundtrips():
    model = json.loads(dm._WEIGHTS_PATH.read_text(encoding="utf-8"))
    assert model["feature_order"] == list(dm.FEATURE_NAMES)
    assert model["weights"] == dm.CURATED_WEIGHTS          # JSON weights == canonical curated
    assert all(w > 0 for w in model["weights"].values())   # every weight positive (didactic sign)
    t1, t2 = model["thresholds"]
    assert t1 < t2
    assert model["fit"]["adjacent_accuracy"] == 1.0        # never off by 2 bands (advisory-safe)


def test_estimate_deterministic_bounded_and_transparent():
    b = _task(kind="create_produce", level="create")
    e1, e2 = dm.estimate(b), dm.estimate(b)
    assert e1.model_dump() == e2.model_dump()               # deterministic
    assert e1.band in (1, 2, 3)
    # contributions sum to the score (transparency: the SME can read the drivers)
    assert abs(sum(e1.contributions.values()) - e1.score) < 1e-9
    assert set(e1.features) == set(dm.FEATURE_NAMES)


# --- 3) fit determinism + consistency with the corpus ------------------------------------

def test_fit_reproduces_on_the_corpus():
    """The fit is deterministic given the data: a fresh scan of the corpus reproduces the
    review-cue count persisted by the fit tool (and reproduces itself run-to-run)."""
    from teachersaid.stats import difficulty_review_cues
    a = difficulty_review_cues()
    b = difficulty_review_cues()
    assert a["count"] == b["count"]                        # run-to-run stable
    shipped = json.loads(dm._WEIGHTS_PATH.read_text(encoding="utf-8"))
    assert a["count"] == shipped["fit"]["review_cue_count"]  # matches the persisted fit


# --- 4) the advisory: fires on disagreement, NEVER mutates the authored value ------------

def _content(task) -> tuple[WorksheetContent, object]:
    res = resolve_kompetenzbereich(PHY, 4, PHY_KB, today=IN)
    # serve a competence that actually resolves, so the coverage check stays clean
    task.serves = [Serves(competence_id=res.competences[0].id, relation="exercises")]
    meta = WorksheetMeta(title="C4-Test", subject=PHY, stufe="Unterstufe", klasse=4,
                         fassung=res.fassung, lehrplan_label=f"{PHY} · 4. Klasse")
    content = WorksheetContent(
        meta=meta, subject_model=ls.get_subject_model(PHY), intro=[],
        sections=[Baustein(id="s1", title="Aufgaben", blocks=[task])])
    return content, res


def test_advisory_fires_on_planted_disagreement_and_never_mutates():
    # authored leicht (difficulty=1) but a create/create_produce task → estimate lands high;
    # |estimate − 1| ≥ 1 → the advisory must flag it as a REVIEW CUE.
    task = _task(kind="create_produce", level="create", difficulty=1)
    est = dm.estimate(task)
    assert est.band >= 2 and est.band - 1 >= 1              # the planted disagreement exists
    content, res = _content(task)
    report = verify(content, res)
    assert report.problems == []                           # advisory lane: never a problem
    hits = [w for w in report.warnings if "Schwierigkeit" in w]
    assert len(hits) == 1 and task.id in hits[0]
    assert "keine Korrektur" in hits[0]                    # worded as a cue, not a correction
    # the load-bearing invariant: verify NEVER overrides the authored difficulty
    assert task.difficulty == 1


def test_advisory_silent_when_estimate_agrees():
    # remember + matching (closed, low kind) authored leicht → estimate band 1 == effective 1
    task = _task(kind="matching", level="remember", difficulty=1,
                 payload=MatchingPayload(left=["a"], right=["b"]))
    assert dm.estimate(task).band == 1
    content, res = _content(task)
    report = verify(content, res)
    assert not any("Schwierigkeit" in w for w in report.warnings)
