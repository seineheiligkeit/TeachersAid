"""Generate (LLM) — schema §7 step 3.

Realises a plan into a WorksheetContent via structured output, then up-converts
the generation view to canonical models. Derived fields are filled later by
assemble(); this stage never produces them.
"""

from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..llm.client import StructuredGenerator, default_generator
from ..llm.prompts import build_system, build_user
from ..schema.generation_views import GenWorksheetBody, body_to_canonical
from ..schema.worksheet import LehrplanResolution, WorksheetContent, WorksheetMeta
from .plan import WorksheetPlan


def _meta(plan: WorksheetPlan, resolution: LehrplanResolution) -> WorksheetMeta:
    kb = (
        resolution.matched_kompetenzbereiche[0]
        if resolution.matched_kompetenzbereiche
        else plan.topic
    )
    return WorksheetMeta(
        title=plan.topic,
        subject=resolution.subject,
        stufe="Unterstufe",
        klasse=resolution.klasse,
        kernfrage=plan.kernfrage,
        fassung=resolution.fassung,
        lehrplan_label=f"{resolution.subject} · {resolution.klasse}. Klasse · {kb}",
    )


def generate_body(
    plan: WorksheetPlan,
    resolution: LehrplanResolution,
    *,
    generator: StructuredGenerator | None = None,
    assets=None,
    extra_notes: list[str] | None = None,
) -> WorksheetContent:
    """Produce a WorksheetContent (WITHOUT derived fields).

    `extra_notes` carries reviewer request-changes feedback into the prompt — this
    is how feedback re-queues into generation.
    """
    subject_model = store.get_subject_model(resolution.subject)
    if subject_model is None:
        raise ValueError(f"no subject model for '{resolution.subject}'")
    gen = generator or default_generator()
    system = build_system(subject_model)
    user = build_user(plan, resolution)
    if extra_notes:
        user += "\n\nReviewer feedback to address in this revision:\n" + "\n".join(
            f"- {n}" for n in extra_notes
        )
    body: GenWorksheetBody = gen.parse(system, user, GenWorksheetBody)
    return body_to_canonical(
        body, meta=_meta(plan, resolution), subject_model=subject_model, assets=assets
    )
