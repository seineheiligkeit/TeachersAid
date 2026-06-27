"""Parametric variant + solution engine (Maths) and inline math typesetting.

The maths is computed (sympy), never authored: variants are correct by construction,
deterministic per seed, and carry a worked Rechenweg. Inline LaTeX runs typeset to images.
"""

from __future__ import annotations

import sympy

from teachersaid.pipeline.parametrize import instantiate, make_variants
from teachersaid.schema.richtext import InlineRun, to_runs

PNG = b"\x89PNG\r\n\x1a\n"


def _template(recipe, tmpl="$x$"):
    from teachersaid.schema.blocks import Serves
    from teachersaid.schema.parametric import ParametricTask
    return ParametricTask(id=recipe, subject="Mathematik", klasse=2,
                          kompetenzbereich="2: Variablen und Funktionen", recipe=recipe,
                          prompt_template=tmpl, serves=[Serves(competence_id="X", relation="exercises")],
                          dimensions=["OPE"])


def test_linear_equation_is_correct_and_deterministic():
    t = _template("linear_equation", "Löse: ${eq}$")
    for seed in (1, 7, 42, 99):
        b = instantiate(t, seed)
        eq = b.prompt[-1].text.replace(" x", "*x")
        lhs, rhs = eq.split("=")
        x = sympy.Symbol("x")
        sol = sympy.solve(sympy.Eq(sympy.sympify(lhs), sympy.sympify(rhs)), x)[0]
        ans = int(b.answer_key[0].text.split("=")[1])
        assert sol == ans                       # the answer actually solves the equation
        assert len(b.solution_steps) == 3
    assert instantiate(t, 7).answer_key[0].text == instantiate(t, 7).answer_key[0].text  # deterministic


def test_percentage_is_correct():
    t = _template("percentage", "Wie viel sind {pct} % von {base}?")
    import re
    for seed in range(5):
        b = instantiate(t, seed)
        pct, base = (int(s) for s in re.findall(r"\d+", b.prompt)[:2])
        assert sympy.sympify(b.answer_key[0].text) == sympy.Rational(base * pct, 100)
        assert b.answer_key[0].math and b.solution_steps


def test_fraction_add_reduced_and_stepped():
    t = _template("fraction_add", "Berechne: ${f1} + {f2}$")
    b = instantiate(t, 3)
    assert b.answer_key[0].math
    assert len(b.solution_steps) == 3          # erweitern · addieren · kürzen
    assert b.prompt[-1].math                    # the operands render as inline math


def test_make_variants_distinct():
    t = _template("linear_equation", "${eq}$")
    vs = make_variants(t, 6)
    assert len({b.prompt[-1].text for b in vs}) >= 4   # mostly distinct
    assert all(b.solution_steps for b in vs)


# --- inline math typesetting -------------------------------------------------
def test_inline_math_renders_to_image(tmp_path):
    from teachersaid.rendering import inline_math
    inline_math.configure(tmp_path)
    res = inline_math.render(r"\frac{3}{4}")
    assert res is not None
    path, w, h = res
    from pathlib import Path
    assert Path(path).read_bytes()[:8] == PNG and w > 0 and h > 0


def test_richtext_markup_math_run(tmp_path):
    from teachersaid.rendering import inline_math, reportlab_base as rb
    inline_math.configure(tmp_path)
    markup = rb.richtext_markup([InlineRun(text="x^2", math=True)])
    assert "<img" in markup and "valign" in markup


def test_math_run_does_not_collapse():
    from teachersaid.schema.richtext import collapse
    runs = [InlineRun(text="\\frac{1}{2}", math=True)]
    assert collapse(runs) == runs                # a lone math run stays a run, not a string


# --- end-to-end: a variant worksheet assembles, verifies, renders ------------
def test_variant_worksheet_assembles_and_verifies():
    from datetime import date
    from teachersaid.library.templates import find_template, variant_worksheet
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.verify import verify
    t = find_template("mat-lineare-gleichung")
    content, res = variant_worksheet(t, 6, today=date(2026, 3, 1))
    assemble(content, res)
    report = verify(content, res)
    assert not report.problems                   # correct-by-construction → verify-clean
    tasks = [b for b in content.iter_blocks() if b.role == "task"]
    assert len(tasks) == 6 and all(b.solution_steps for b in tasks)


def test_all_templates_instantiate_and_verify_clean():
    from datetime import date
    from teachersaid.library.templates import PARAM_TEMPLATES, variant_worksheet
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.verify import verify
    assert len(PARAM_TEMPLATES) >= 10
    for t in PARAM_TEMPLATES:
        content, res = variant_worksheet(t, 4, today=date(2026, 3, 1))
        assemble(content, res)
        report = verify(content, res)
        assert not report.problems, f"{t.id}: {report.problems}"
        tasks = [b for b in content.iter_blocks() if b.role == "task"]
        assert len(tasks) == 4 and all(b.solution_steps for b in tasks), t.id


def test_pythagoras_and_geometry_correct():
    import re
    t = _template("pythagoras", "$a={a}$ $b={b}$")
    for seed in range(8):
        b = instantiate(t, seed)
        a, bb = (int(x) for x in re.findall(r"\d+", "".join(r.text for r in b.prompt)))
        c = int(b.answer_key[0].text.split("=")[1])
        assert a * a + bb * bb == c * c          # a real Pythagorean triple
    r = instantiate(_template("rectangle", "{l}x{w}"), 5)
    assert "cm²" in r.answer_key and "u =" in r.answer_key


def test_compose_variants_stages_item(tmp_path):
    from datetime import date
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.repository import ReviewStore
    store = ReviewStore(tmp_path)
    item = orch.compose_variants(store, "mat-prozent", 5, today=date(2026, 3, 1))
    assert item.error is None and item.content is not None
    assert not item.verify_problems
    # the teacher PDF carries the Rechenweg label (text), inline math is images
    import fitz
    t = "".join(p.get_text() for p in fitz.open(item.artifacts.teacher_pdf))
    assert "Rechenweg" in t
