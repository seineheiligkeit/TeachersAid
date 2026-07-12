"""Textlast (P3 Tiefenregler) — the simplified-prose-twin fader helpers.

The Textlast fader has two endpoints: ``voll`` (the unchanged master prompt, full register)
and ``einfach`` (the template's APPROVED simplified twin — ``ParametricTask.prompt_simple`` —
plus, where curated, a student-facing Wortschatz-Kasten from ``ParametricTask.glossary``).

Crucially the fader is a SELECTION between two CURATED, SME-vetted fields, not a fader-time
rewrite: the twin carries the master's exact ``{slots}`` (validated on the schema, so the SAME
computed values fill it), and no factual value is ever touched — the projection is the same
shape as rendering.  The twin is applied in ``pipeline/parametrize._instantiate`` (a straight
``prompt_simple.format(**params)``); this module owns only the *measurement* the Regler-Lint
needs and the verbatim-text guard.

Measurement.  ``measure_wstf`` runs the ONE readability formula the project already has (the
Erste Wiener Sachtextformel, ``pipeline/readability``) over the concatenated STUDENT-FACING
task-prompt prose of a variant set — the passage a student must read to understand the tasks.
It is measured over the whole set (not per prompt) because a single short prompt is below the
WSTF word threshold; N near-identical variants of one template give a stable, measurable
passage.  Math runs are skipped (they are not German prose) and numbers do not count as words,
so the metric moves on REGISTER (word/sentence complexity), not on the drawn values.

Verbatim guard (structural, not by convention).  ``student_prose`` excludes any block the
readability lint marks ``advisory_exempt`` — a ``source_text`` block or a ``quoted``-provenance
block is verbatim selected material that is not ours to simplify (an authentic Lesetext is
deliberately hard; its difficulty is the point).  The Textlast fader's only writable input is
``ParametricTask.prompt_simple``, which exists solely on parametric templates (authored, never
verbatim); this guard makes that boundary explicit and testable.
"""

from __future__ import annotations

from ..schema.blocks import TaskBlock
from ..schema.enums import Role
from . import readability


def _twinnable(block) -> bool:
    """True if a block's prompt prose may be measured/simplified: a task block whose prose is
    NOT verbatim selected material (see the verbatim guard in the module docstring)."""
    return block.role == Role.TASK and not readability.advisory_exempt(block)


def student_prose(blocks: list[TaskBlock]) -> str:
    """The concatenated student-facing prompt prose of the twinnable tasks (verbatim-exempt
    blocks skipped, math runs skipped) — the passage the WSTF metric measures."""
    return " ".join(
        readability.extract_prose(b.prompt) for b in blocks if _twinnable(b)
    ).strip()


def measure_wstf(blocks: list[TaskBlock]) -> float | None:
    """Wiener Sachtextformel Schulstufe over the student-facing task prose, or None when there
    is too little of it to mean anything (below the readability word threshold)."""
    prose = student_prose(blocks)
    return readability.wstf(prose) if prose else None
