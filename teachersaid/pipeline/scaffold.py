"""Gerüst (P2 Tiefenregler) — the scaffold builder.

The Gerüst fader projects the SAME seeded parametric instance into a scaffolded twin by
attaching a `schema.blocks.TaskScaffold` to each task.  Every scaffold element is DERIVED
from computed/curated data — never freshly authored didactic prose — and, crucially, is
STUDENT-FACING, so each element is built so that it can never leak the answer:

  (a) a worked FIRST step from the instance's `solution_steps[0]` (never the full Rechenweg),
      admitted only when a deterministic leak-guard proves the answer is absent from it, and
      never for mapping kinds (matching/ordering), whose first step *is* a pairing;
  (b) a misconception warning wherever the instance carries `MCSpec` — it names the trap
      CATEGORY from the curated `grounding/misconceptions` catalog (never the answer);
  (c) curated Formulierungshilfen (sentence starters) for prose response surfaces — the one
      authored surface in the fader, kept small and generic and SME-vettable.

`build_scaffold` returns `None` when a task exposes none of the three, so the mixer can
hard-reject a template that cannot move the metric (never a no-op control).

Leak-guard (the load-bearing safety property).  The worked first step is admitted iff the
answer does not appear in it.  For a numeric answer we compare the *values* the answer and
the step contain, parsed fraction-aware (a `\\frac{a}{b}` or `a/b` is one atomic value, so a
common denominator shown in the step is not mistaken for the answer, and an exponent is
stripped so `c^2` never reads as the value 2).  For a pure-text answer we fall back to a
normalised substring test.  The guard errs to the SAFE side: a coincidental value match
merely drops that one worked step (the other elements still scaffold the task).
"""

from __future__ import annotations

import re

from ..grounding import misconceptions as _cat
from ..schema.blocks import SolutionStep, TaskBlock, TaskScaffold
from ..schema.parametric import Instance
from ..schema.richtext import InlineRun, RichText, plain_text

# Mapping kinds get no worked first step: their "first solution step" reveals a pairing, i.e.
# part of the answer.  (MC is fine — its first step is a formula/setup, not an option.)
_NO_WORKED_STEP_KINDS = frozenset({"matching", "ordering"})

# Formulierungshilfen (sentence starters) — a SMALL curated table, keyed by task kind.
# German, Austrian school register; deliberately generic so a starter fits ANY item of that
# kind and can never touch a datum the task computes.  This is the ONE authored surface in
# the Gerüst fader (every other element is derived) — SME-vettable.
_FORMULIERUNGSHILFEN: dict[str, list[str]] = {
    "open_response": [
        "Zuerst überlege ich, was gegeben und was gesucht ist: …",
        "Mein Lösungsweg: zuerst …, dann …",
        "Daraus folgt, dass …, weil …",
    ],
    "decision_scenario": [
        "Ich entscheide mich für …, weil …",
        "Dafür spricht …",
        "Dagegen spricht … — dennoch …",
    ],
    "true_false_justify": [
        "Die Aussage ist richtig / falsch, weil …",
        "Ein Beispiel, das das zeigt, ist …",
    ],
    "modelling_task": [
        "Gegeben ist … , gesucht ist …",
        "Ich stelle den Zusammenhang so auf: …",
        "In Worten bedeutet mein Ergebnis: …",
    ],
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _numeric_values(s: str) -> set[float]:
    """The set of numeric values a string contains, parsed FRACTION-AWARE (a fraction is one
    atomic value, not two integers) and with exponents stripped (`c^2` is not the value 2)."""
    s = re.sub(r"\^\{[^}]*\}", " ", s)           # strip \^{...}
    s = re.sub(r"\^-?\d+", " ", s)               # strip \^2
    vals: set[float] = set()
    for m in re.finditer(r"\\frac\{(-?\d+)\}\{(-?\d+)\}", s):
        if int(m.group(2)) != 0:
            vals.add(round(int(m.group(1)) / int(m.group(2)), 4))
    s = re.sub(r"\\frac\{-?\d+\}\{-?\d+\}", " ", s)
    for m in re.finditer(r"(-?\d+)\s*/\s*(-?\d+)", s):   # plain a/b fractions
        if int(m.group(2)) != 0:
            vals.add(round(int(m.group(1)) / int(m.group(2)), 4))
    s = re.sub(r"-?\d+\s*/\s*-?\d+", " ", s)
    for m in re.finditer(r"-?\d+(?:[.,]\d+)?", s):       # remaining ints / decimals
        vals.add(round(float(m.group(0).replace(",", ".")), 4))
    return vals


def _plain(rt: RichText | None) -> str:
    if rt is None:
        return ""
    return rt if isinstance(rt, str) else plain_text(rt)


def _step_text(step: SolutionStep) -> str:
    return f"{_plain(step.text)} {step.expr or ''}"


def _leaks_answer(step: SolutionStep, block: TaskBlock) -> bool:
    """True if the block's answer is present in `step` (so showing it would leak the result)."""
    answer = _plain(block.answer_key)
    if not answer:
        return False
    step_str = _step_text(step)
    answer_vals = _numeric_values(answer)
    if answer_vals:                                   # numeric answer → compare values
        return bool(answer_vals & _numeric_values(step_str))
    ans_norm = _norm(answer)                          # pure-text answer → substring test
    return bool(ans_norm) and ans_norm in _norm(step_str)


def _worked_first_step(block: TaskBlock, instance: Instance) -> RichText | None:
    """The leak-guarded worked FIRST step as student-facing RichText, or None."""
    if block.kind in _NO_WORKED_STEP_KINDS or not instance.steps:
        return None
    step = instance.steps[0]
    if _leaks_answer(step, block):
        return None
    text = step.text
    runs: list[InlineRun] = [InlineRun(text=text)] if isinstance(text, str) else list(text)
    if step.expr:
        runs.append(InlineRun(text="  "))
        runs.append(InlineRun(text=step.expr, math=True))
    return runs


def _misconception_hint(instance: Instance) -> tuple[str | None, list[str]]:
    """A student warning naming the trap CATEGORIES the recipe's distractors probe (never the
    answer), sourced from the curated catalog; plus the category names for the teacher line."""
    ids: list[str] = []
    for d in instance.mc_distractors:
        if d.misconception_id not in ids:
            ids.append(d.misconception_id)
    if not ids:
        return None, []
    names = [_cat.get(i).name for i in ids]
    hint = ("Achtung – hier passieren oft Fehler (" + ", ".join(names)
            + "). Rechne Schritt für Schritt und überprüfe dein Ergebnis am Ende.")
    return hint, names


def _formulierungshilfen(block: TaskBlock) -> list[str]:
    return list(_FORMULIERUNGSHILFEN.get(block.kind, []))


def build_scaffold(block: TaskBlock, instance: Instance) -> TaskScaffold | None:
    """Compute the Gerüst scaffold for one instantiated task, or None if the task exposes no
    scaffoldable data (no leak-free first step, no misconception hint, no prose surface)."""
    first_step = _worked_first_step(block, instance)
    hint, categories = _misconception_hint(instance)
    starters = _formulierungshilfen(block)
    if not (first_step or hint or starters):
        return None
    return TaskScaffold(
        first_step=first_step,
        hint=hint,
        hint_categories=categories,
        sentence_starters=starters,
    )


def scaffold_size(scaffold: TaskScaffold | None) -> int:
    """Total scaffold elements (a worked step + a hint + each Formulierungshilfe)."""
    if scaffold is None:
        return 0
    return (bool(scaffold.first_step) + bool(scaffold.hint)
            + len(scaffold.sentence_starters))
