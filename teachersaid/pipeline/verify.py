"""Verify (rules + optional LLM) — schema §7 step 4.

Bounded checks only — this is where difficulty calibration lives as a small,
well-defined surface (the open hard problem), NOT a structural rewrite:
* structural: task kinds + dimensions legal for the subject model;
* coverage: every `serves` references a resolved competence;
* depth: the DepthTarget ladder is actually met;
* difficulty: every task has a positive time estimate and a cognitive level;
* media policy: each asset satisfies the library-entry gate (content-bearing →
  code-gen/vetted-sourced; decorative → content-free). See `media_policy.py`.
An LLM fact-check of VerificationItems is optional and skipped without a key.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..schema.enums import COGNITIVE_RANK, Role
from ..schema.worksheet import LehrplanResolution, WorksheetContent
from .assemble import validate_against_model
from .derive import compute_depth
from .media_policy import check_content
from .plan import WorksheetPlan


class VerifyReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool = True
    problems: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def verify(
    content: WorksheetContent,
    resolution: LehrplanResolution,
    *,
    plan: WorksheetPlan | None = None,
) -> VerifyReport:
    problems: list[str] = []
    warnings: list[str] = []

    # structural
    problems += validate_against_model(content)

    # media policy: the asset library-entry gate (content-bearing must be correct,
    # decorative must be content-free)
    mp_problems, mp_warnings = check_content(content)
    problems += mp_problems
    warnings += mp_warnings

    # chart representation sanity (a correct number badly represented is still wrong)
    from .chart_lint import lint_content as _lint_charts
    cl_problems, cl_warnings = _lint_charts(content)
    problems += cl_problems
    warnings += cl_warnings

    # coverage: serves must reference resolved competences
    valid_ids = {c.id for c in resolution.competences}
    for b in content.iter_blocks():
        if b.role != Role.TASK:
            continue
        for s in b.serves:
            if valid_ids and s.competence_id not in valid_ids:
                problems.append(
                    f"{b.id}: serves unknown competence '{s.competence_id}'"
                )
        # difficulty sanity
        if b.est_minutes <= 0:
            warnings.append(f"{b.id}: missing/zero est_minutes")
        if b.cognitive_level not in COGNITIVE_RANK:
            problems.append(f"{b.id}: invalid cognitive_level '{b.cognitive_level}'")

    # difficulty calibration (3d): flag a flat Anforderungs-spectrum (advisory)
    from .difficulty import DIFFICULTY_LABEL, effective_difficulty
    task_blocks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    diffs = {effective_difficulty(b) for b in task_blocks}
    if len(task_blocks) >= 3 and len(diffs) == 1:
        warnings.append(
            f"Anforderungsniveau flach: alle {len(task_blocks)} Aufgaben auf "
            f"'{DIFFICULTY_LABEL[next(iter(diffs))]}' — kein Spektrum"
        )

    # depth target met?
    if plan is not None and plan.depth_target.min_at_or_above:
        target = plan.depth_target.min_at_or_above
        floor = COGNITIVE_RANK.get(target["level"], 99)
        dp = compute_depth(content)
        at_or_above = sum(
            cnt for lvl, cnt in dp.by_level.items()
            if COGNITIVE_RANK.get(lvl, -1) >= floor
        )
        if at_or_above < target["count"]:
            warnings.append(
                f"depth target not met: {at_or_above} task(s) at "
                f"'{target['level']}'+ (wanted {target['count']})"
            )
        ri_need = plan.depth_target.require_resource_independent_minutes
        if ri_need and dp.minutes_resource_independent < ri_need:
            warnings.append(
                f"only {dp.minutes_resource_independent} resource-independent min "
                f"(wanted ≥{ri_need})"
            )

    return VerifyReport(ok=not problems, problems=problems, warnings=warnings)
