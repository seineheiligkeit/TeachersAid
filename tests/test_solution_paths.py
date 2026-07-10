"""Solution graphs (roadmap A4) — the alternative Lösungswege on parametric recipes.

Locks the load-bearing guarantees: a recipe emits ONE primary Rechenweg (`solution_steps`)
plus the OTHER legitimate school strategies as `solution_paths`, every one DERIVED (sympy,
exact) and reaching the IDENTICAL answer. Where strategies genuinely diverge:

* LGS(2) → Additionsverfahren (primary) + Einsetzungs- + Gleichsetzungsverfahren.
* Prozentwert / Prozentsatz → Prozentformel (primary) + Dreisatz + Prozentoperator.

Plus: per-seed determinism; the generation view CANNOT carry solution_paths (the derivation
lock, mirroring solution_steps); the teacher guide renders "Alternative Lösungswege" + the
strategy names, the student sheet renders none of it; and LGS(3) stays single-path (no
artificial alternatives — Gauß/Addition is the natural route). Zero LLM: all derived.
"""

from __future__ import annotations

import re
from datetime import date

import sympy

from teachersaid.pipeline.parametrize import instantiate, make_variants
from teachersaid.schema.blocks import Serves
from teachersaid.schema.parametric import ParametricTask
from teachersaid.schema.richtext import plain_text

IN_WINDOW = date(2026, 3, 1)


def _mk(recipe: str, tmpl: str, klasse: int = 6) -> ParametricTask:
    return ParametricTask(
        id=recipe, subject="Mathematik", klasse=klasse,
        kompetenzbereich="1: Zahlen und Maße", recipe=recipe, prompt_template=tmpl,
        serves=[Serves(competence_id="X", relation="exercises")], dimensions=["OPE"])


_LGS2 = _mk("linear_system_2", "${eq1}$ und ${eq2}$")
_PCT = _mk("percentage", "Wie viel sind {pct} % von {base}?", klasse=2)
_RATE = _mk("percentage_rate", "Wie viel Prozent sind {part} von {base}?", klasse=2)


# ============================================================================
# LGS(2): exactly the three named strategies, each independently correct
# ============================================================================
def test_lgs2_emits_exactly_three_named_strategies():
    """Primary Rechenweg is present; the two alternatives are exactly the Einsetzungs- and
    Gleichsetzungsverfahren (the primary Additionsverfahren is NOT duplicated among them)."""
    for seed in range(1, 80):
        b = instantiate(_LGS2, seed)
        assert b.solution_steps, seed                       # a primary Rechenweg exists
        names = [p.strategy for p in b.solution_paths]
        assert names == ["Einsetzungsverfahren", "Gleichsetzungsverfahren"], (seed, names)
        # every path carries worked steps and the primary is never repeated as an "alternative"
        assert all(p.steps for p in b.solution_paths)
        assert "Additionsverfahren" not in names


def _lgs_equations_from_prompt(b) -> tuple[sympy.Eq, sympy.Eq]:
    """Recover (I, II) as sympy equations from the two math runs on the prompt."""
    from teachersaid.schema.richtext import to_runs
    math_runs = [r.text for r in to_runs(b.prompt) if r.math]
    assert len(math_runs) == 2, math_runs
    eqs = []
    for tex in math_runs:
        # insert an explicit '*' only between a DIGIT and a spaced variable ("2 x" → "2*x");
        # a bare "- y" (coefficient ±1) must be left alone (sympify reads "-y" fine).
        norm = re.sub(r"(\d)\s+([xy])", r"\1*\2", tex)
        lhs, rhs = norm.split("=")
        eqs.append(sympy.Eq(sympy.sympify(lhs), sympy.sympify(rhs)))
    return eqs[0], eqs[1]


def test_lgs2_every_path_solves_the_same_system_to_the_same_answer():
    """The strongest check: recover the system from the prompt, solve it independently with
    sympy, and confirm BOTH the primary answer AND every alternative path lead there. (The
    recipe already asserts path/linsolve agreement at build time; this re-derives from the
    rendered artifact, so the guarantee survives the whole pipeline.)"""
    x, y = sympy.symbols("x y")
    for seed in range(1, 120):
        b = instantiate(_LGS2, seed)
        eq1, eq2 = _lgs_equations_from_prompt(b)
        sol = sympy.solve([eq1, eq2], [x, y])
        sx, sy = sol[x], sol[y]
        # the stated answer matches the independent solve
        ans = "".join(r.text for r in b.answer_key)
        m = re.search(r"x = (-?\d+),\\; y = (-?\d+)", ans)
        assert m, ans
        assert (int(m.group(1)), int(m.group(2))) == (sx, sy), (seed, ans, sx, sy)
        # and the final step of each alternative path states that same (x, y)
        for p in b.solution_paths:
            joined = " ".join(st.expr or "" for st in p.steps)
            assert f"x = {sympy.latex(sx)}" in joined, (seed, p.strategy, "x missing")
            # y appears either as an explicit "y = <val>" step or inside the x-back-substitution
            assert f"y = {sympy.latex(sy)}" in joined or f"= {sympy.latex(sy)}" in joined, \
                (seed, p.strategy, "y missing")


def test_lgs3_stays_single_path():
    """LGS(3) is Addition/Gauß by nature — no artificial alternatives are forced."""
    t = _mk("linear_system_3", "${eq1}$, ${eq2}$, ${eq3}$")
    for seed in range(1, 40):
        b = instantiate(t, seed)
        assert b.solution_steps and b.solution_paths == [], seed


# ============================================================================
# Prozentrechnung: Dreisatz + Prozentoperator, both re-derived to the answer
# ============================================================================
def test_percentage_emits_dreisatz_and_operator():
    for t in (_PCT, _RATE):
        for seed in range(1, 80):
            b = instantiate(t, seed)
            assert b.solution_steps, (t.recipe, seed)       # primary = Prozentformel
            names = [p.strategy for p in b.solution_paths]
            assert names == ["Dreisatz", "Prozentoperator"], (t.recipe, seed, names)
            assert all(p.steps for p in b.solution_paths)


def _percent_answer_value(b) -> sympy.Rational:
    """The rendered primary answer as an exact value. Handles the three forms it takes: a
    plain string ('15 %'), an integer LaTeX run ('20'), and a fraction run ('\\frac{45}{2}')."""
    tex = b.answer_key if isinstance(b.answer_key, str) else plain_text(b.answer_key)
    frac = re.search(r"\\frac\{(-?\d+)\}\{(-?\d+)\}", tex)
    if frac:
        return sympy.Rational(int(frac.group(1)), int(frac.group(2)))
    return sympy.Rational(re.search(r"-?\d+", tex).group(0))


def test_percentage_paths_recompute_to_the_primary_answer():
    """Recompute each strategy's value independently from the drawn numbers in the prompt and
    require it to equal the primary answer — the equal-answer invariant, re-checked from the
    rendered item (the recipe also asserts this at build time via _assert_percent_value)."""
    # percentage: "Wie viel sind p % von G?" → answer = G·p/100 by every route
    for seed in range(1, 120):
        b = instantiate(_PCT, seed)
        pct, base = (int(s) for s in re.findall(r"\d+", plain_text(b.prompt))[:2])
        ans = _percent_answer_value(b)
        formel = sympy.Rational(base * pct, 100)
        dreisatz = sympy.Rational(base, 100) * pct
        operator = base * sympy.Rational(pct, 100)
        assert formel == dreisatz == operator == ans, (seed, pct, base, ans)
    # percentage_rate: "Wie viel Prozent sind W von G?" → answer = W/G·100
    for seed in range(1, 120):
        b = instantiate(_RATE, seed)
        part, base = (int(s) for s in re.findall(r"\d+", plain_text(b.prompt))[:2])
        ans = _percent_answer_value(b)
        formel = sympy.Rational(part, base) * 100
        dreisatz = sympy.Rational(100, base) * part
        operator = sympy.Rational(part, base) * 100
        assert formel == dreisatz == operator == ans, (seed, part, base, ans)


# ============================================================================
# determinism
# ============================================================================
def test_solution_paths_deterministic_per_seed():
    """Same seed → identical primary steps AND identical alternative paths (strategy names,
    step texts, exprs, notes)."""
    for t in (_LGS2, _PCT, _RATE):
        for seed in (1, 7, 42, 99):
            a = instantiate(t, seed)
            b = instantiate(t, seed)
            assert [(s.text, s.expr) for s in a.solution_steps] == \
                   [(s.text, s.expr) for s in b.solution_steps], (t.recipe, seed)
            assert len(a.solution_paths) == len(b.solution_paths)
            for pa, pb in zip(a.solution_paths, b.solution_paths):
                assert pa.strategy == pb.strategy and pa.note == pb.note
                assert [(s.text, s.expr) for s in pa.steps] == \
                       [(s.text, s.expr) for s in pb.steps], (t.recipe, seed, pa.strategy)


def test_make_variants_carries_paths_on_every_variant():
    for t in (_LGS2, _PCT, _RATE):
        vs = make_variants(t, 5, seed0=1)
        assert all(len(b.solution_paths) == 2 for b in vs), t.recipe


# ============================================================================
# the derivation lock: the LLM can never author solution_paths
# ============================================================================
def test_generation_view_cannot_carry_solution_paths():
    """`GenTaskBlock` has NO solution_paths field (absence-by-omission, exactly like
    solution_steps): the LLM's schema cannot express it, and up-conversion never fills it,
    so a derived alternative path can only come from the pipeline engine."""
    from teachersaid.schema.generation_views import GenTaskBlock
    from teachersaid.schema.response import LinesResponse

    assert "solution_paths" not in GenTaskBlock.model_fields
    assert "solution_steps" not in GenTaskBlock.model_fields   # the sibling it mirrors
    # extra="forbid" → even smuggling the key into the JSON is rejected
    import pydantic
    payload = dict(role="task", id="t1", kind="calculation", prompt="p",
                   response=LinesResponse(n=2).model_dump(), cognitive_level="apply",
                   solution_paths=[{"strategy": "Hack", "steps": []}])
    try:
        GenTaskBlock.model_validate(payload)
        raise AssertionError("GenTaskBlock accepted a solution_paths key")
    except pydantic.ValidationError:
        pass
    # and a clean up-converted block starts with no alternatives
    from teachersaid.schema.generation_views import _task_to_canonical
    g = GenTaskBlock(role="task", id="t2", kind="calculation", prompt="p",
                     response=LinesResponse(n=2), cognitive_level="apply")
    assert _task_to_canonical(g).solution_paths == []


# ============================================================================
# rendering: teacher shows the alternatives, student/homework never do
# ============================================================================
def test_teacher_renders_alternatives_student_does_not(tmp_path):
    import fitz
    from teachersaid.library.templates import find_template, variant_worksheet
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.rendering.homework import render_homework
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide

    t = find_template("mat-os-lgs2")
    content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
    content = assemble(content, res)
    sp = render_student_sheet(content, tmp_path / "s.pdf")
    tp = render_teacher_guide(content, tmp_path / "t.pdf")
    hp = render_homework(content, tmp_path / "h.pdf")
    stud = "".join(p.get_text() for p in fitz.open(sp))
    teach = "".join(p.get_text() for p in fitz.open(tp))
    home = "".join(p.get_text() for p in fitz.open(hp))

    # teacher: the section header + the "Schüler könnten auch (…)" leads + strategy names
    assert "Alternative Lösungswege" in teach
    assert "Schüler könnten auch" in teach
    assert "Einsetzungsverfahren" in teach and "Gleichsetzungsverfahren" in teach
    # student + homework: none of it leaks (these are student-facing)
    for text in (stud, home):
        assert "Alternative Lösungswege" not in text
        assert "Schüler könnten" not in text
        assert "Einsetzungsverfahren" not in text


def test_percentage_teacher_shows_dreisatz_operator(tmp_path):
    import fitz
    from teachersaid.library.templates import find_template, variant_worksheet
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide

    t = find_template("mat-prozent")
    content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
    content = assemble(content, res)
    sp = render_student_sheet(content, tmp_path / "s.pdf")
    tp = render_teacher_guide(content, tmp_path / "t.pdf")
    stud = "".join(p.get_text() for p in fitz.open(sp))
    teach = "".join(p.get_text() for p in fitz.open(tp))
    assert "Alternative Lösungswege" in teach
    assert "Dreisatz" in teach and "Prozentoperator" in teach
    assert "Dreisatz" not in stud and "Alternative" not in stud


# ============================================================================
# the templates that use these recipes still assemble + verify clean
# ============================================================================
def test_solution_path_templates_verify_clean():
    from teachersaid.library.templates import find_template, variant_worksheet
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.verify import verify
    for tid in ("mat-os-lgs2", "mat-prozent", "mat-prozentsatz"):
        t = find_template(tid)
        content, res = variant_worksheet(t, 4, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert not rep.problems, (tid, rep.problems)
        tasks = [b for b in content.iter_blocks() if b.role == "task"]
        assert len(tasks) == 4
        assert all(b.solution_steps and b.solution_paths for b in tasks), tid
