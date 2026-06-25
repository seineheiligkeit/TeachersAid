"""Prompt builders for the generation stage.

Working language is English (the team's); the PRODUCT output is German. The open
TaskKind / CognitiveLevel sets are injected here as text (not as closed JSON
enums) so the generation view stays a robust structured-output contract.
"""

from __future__ import annotations

from ..schema.competence import SubjectCompetenceModel
from ..schema.enums import CORE_TASK_KINDS
from ..schema.worksheet import LehrplanResolution
from ..pipeline.plan import WorksheetPlan

_COGNITIVE = ["remember", "understand", "apply", "analyze", "evaluate", "create"]


def build_system(model: SubjectCompetenceModel) -> str:
    kinds = sorted(CORE_TASK_KINDS | set(model.task_kind_extensions))
    dims = ", ".join(f"{d.id} ({d.label})" for d in model.dimensions)
    return (
        "You generate Austrian-Lehrplan-anchored teaching material. The worksheet "
        "TEXT must be in German and at AHS Unterstufe level (never below it — the "
        "incumbent failed on examples that were 'zu niedrig für AHS').\n\n"
        "Hard rules:\n"
        f"- Allowed task `kind` values: {', '.join(kinds)}. Use exactly these strings.\n"
        f"- Allowed `dimensions` (DimensionRefs): {dims}. Put the primary first.\n"
        f"- Allowed `cognitive_level`: {', '.join(_COGNITIVE)}.\n"
        "- Depth = cognitive demand, not word count. Make tasks climb a ladder and "
        "be resource-independent where possible.\n"
        "- Correctness by construction: never assert a fact you are unsure of; put "
        "anything a teacher must watch for in `watch_outs` (load-bearing).\n"
        "- Each task's `serves` must reference one of the given competence ids.\n"
        "- Do NOT invent coverage you did not write; a competence left unexercised is "
        "fine and will be surfaced as a gap downstream.\n"
        "- Student-facing text (prompts, options, intro) is for the STUDENTS: never "
        "mention competence ids, dimensions, or the Lehrplan in it.\n"
        "- For EACH section, also write a teacher layer (shown only on the teacher "
        "guide, never to students): `throughline` (the Roter Faden in one sentence), "
        "`talking_points` (2–4 discussion anchors / questions to pose in class), and "
        "`extensions` (1–3 going-further or differentiation ideas). The teacher already "
        "knows the topic — make these genuinely useful, not a restatement of the tasks.\n"
        "- Per task, the `answer_key` is the expected answer and `watch_outs` the "
        "misconceptions; these are the teacher's, not printed for students.\n"
        "- Emit ONLY the structured body (intro + sections of blocks). Do not write a "
        "Nachweis or depth profile — those are derived."
    )


def build_user(plan: WorksheetPlan, resolution: LehrplanResolution) -> str:
    lines = [
        f"Topic: {plan.topic}",
        f"Subject: {plan.subject}, Klasse {plan.klasse}",
        f"Kernfrage: {plan.kernfrage}",
        f"Time budget: ~{plan.minutes_budget} min",
        "",
        "Resolved competences (verbatim — anchor tasks to these):",
    ]
    for c in resolution.competences:
        ut = f" [ÜT {','.join(map(str, c.uebergreifende_themen))}]" if c.uebergreifende_themen else ""
        lines.append(f"  - {c.id} (dims {','.join(c.dimensions)}){ut}: {c.text.strip()}")
    lines += ["", "Block-spec skeleton to realise (fill each spec with real German content):"]
    for sec in plan.section_specs:
        lines.append(f"  Section '{sec.title}' — throughline: {sec.throughline}")
        for bs in sec.block_specs:
            lines.append(
                f"    * spec {bs.suggested_id}: kind={bs.kind}, level={bs.cognitive_level}, "
                f"dim={bs.dimension}, serves={bs.serves_competence_id}, "
                f"~{bs.est_minutes}min — {bs.intent}"
            )
    dt = plan.depth_target
    if dt.min_at_or_above:
        lines.append(
            f"\nDepth target: at least {dt.min_at_or_above['count']} tasks at "
            f"'{dt.min_at_or_above['level']}' or higher; "
            f"≥{dt.require_resource_independent_minutes} resource-independent minutes."
        )
    lines.append(
        "\nYou may add a short intro InfoBlock and additional tasks if they raise "
        "depth, but stay within the topic and the allowed kinds/dimensions."
    )
    return "\n".join(lines)
