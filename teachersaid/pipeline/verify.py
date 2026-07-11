"""Verify (rules + optional LLM) — schema §7 step 4.

Bounded checks only — this is where difficulty calibration lives as a small,
well-defined surface (the open hard problem), NOT a structural rewrite:
* structural: task kinds + dimensions legal for the subject model;
* coverage: every `serves` references a resolved competence;
* depth: the DepthTarget ladder is actually met;
* difficulty: every task has a positive time estimate and a cognitive level;
* media policy: each asset satisfies the library-entry gate (content-bearing →
  code-gen/vetted-sourced; decorative → content-free). See `media_policy.py`.
* readability (advisory, roadmap A6): the Wiener Sachtextformel per prose block,
  flagged when far above the worksheet's target Schulstufe. See `readability.py`.
An LLM fact-check of VerificationItems is optional and skipped without a key.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..schema.enums import AnchorMode, COGNITIVE_RANK, Role
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

    # primary anchoring trust gate. Kompetenz uses the supplied resolution; ÜT is
    # checked against the exact subject/grade catalog hook; Horizont must not carry
    # a hidden competence claim.
    if content.anchor_mode == AnchorMode.UET:
        from ..grounding import lehrplan_store as _ls
        stufe = _ls.stufe_for_klasse(content.meta.klasse)
        legend = _ls.uebergreifende_themen(stufe)
        if content.anchor_uet not in legend:
            problems.append(
                f"anchor: ÜT {content.anchor_uet} ist im {stufe}-Katalog nicht definiert"
            )
            anchor_valid_ids: set[str] = set()
        else:
            anchor_valid_ids = {
                c.id for c in _ls.competences_for(
                    content.meta.subject, content.meta.klasse, stufe
                ) if content.anchor_uet in c.uebergreifende_themen
            }
            if not anchor_valid_ids:
                problems.append(
                    f"anchor: {content.meta.subject} führt ÜT {content.anchor_uet} "
                    f"in der {content.meta.klasse}. Klasse nicht als verbatim Hook"
                )
    elif content.anchor_mode == AnchorMode.HORIZONT:
        anchor_valid_ids = set()
    else:
        anchor_valid_ids = {c.id for c in resolution.competences}

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

    # grounded-facts (c)-label: a data figure must declare sourced vs illustrative
    from .figure_lint import lint_content as _lint_figures
    fl_problems, fl_warnings = _lint_figures(content)
    problems += fl_problems
    warnings += fl_warnings

    # numeric claims: task prose next to a SOURCED figure must derive from the
    # cited dataset slice (the last authored-number hole; also the anti-rot check)
    from .number_lint import lint_content as _lint_numbers
    nl_problems, nl_warnings = _lint_numbers(content)
    problems += nl_problems
    warnings += nl_warnings

    # expression provenance (History/GPB): a history fact block records its facts-source,
    # and an embedded source's obligation is coherent (the prose analogue of the (c)-label)
    from .prose_lint import lint_content as _lint_prose
    pl_problems, pl_warnings = _lint_prose(content)
    problems += pl_problems
    warnings += pl_warnings

    # readability (advisory, roadmap A6): a prose/task block far above the worksheet's
    # target Schulstufe (German syllable counting is heuristic — never a gate, see
    # readability.py's module docstring for the honesty-required rationale)
    from .readability import (
        SCHULSTUFE_OVERSHOOT_WARN, advisory_exempt, estimate_block,
        klasse_to_schulstufe,
    )
    target_stufe = klasse_to_schulstufe(content.meta.klasse)
    for b in content.iter_blocks():
        if advisory_exempt(b):  # verbatim sources are deliberately hard — not ours to simplify
            continue
        est = estimate_block(b)
        if est is not None and est - target_stufe > SCHULSTUFE_OVERSHOOT_WARN:
            est_de = f"{est:.1f}".replace(".", ",")
            warnings.append(
                f"{b.id}: Lesbarkeit (Wiener Sachtextformel) geschätzt auf Schulstufe "
                f"{est_de} — deutlich über der Zielstufe {target_stufe} (Klasse "
                f"{content.meta.klasse}) — Text ggf. vereinfachen (kürzere Sätze, "
                f"weniger Mehrsilbler)."
            )

    # coverage: serves must reference resolved competences
    for b in content.iter_blocks():
        if b.role != Role.TASK:
            continue
        if content.anchor_mode == AnchorMode.HORIZONT and b.serves:
            problems.append(
                f"{b.id}: Horizont darf keinen Lehrplan-Kompetenzbezug über `serves` behaupten"
            )
        for s in b.serves:
            if s.competence_id not in anchor_valid_ids:
                problems.append(
                    f"{b.id}: serves competence '{s.competence_id}' außerhalb des "
                    f"Verankerungsmodus '{content.anchor_mode}'"
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

    # difficulty model (C4): a COMPUTED second opinion. When the estimate from the task's
    # own surface features disagrees with the operative difficulty by ≥1 band, flag it as a
    # REVIEW CUE — never a correction, never overriding the authored value (advisory lane).
    from .difficulty_model import estimate as _diff_estimate, top_drivers
    for b in task_blocks:
        est = _diff_estimate(b)
        if est is None:
            continue
        eff = effective_difficulty(b)
        if abs(est.band - eff) < 1:
            continue
        authored = getattr(b, "difficulty", None) in (1, 2, 3)
        quelle = "SME-Schätzung" if authored else "aus Anforderungsbereich abgeleitet"
        richtung = "wirkt anspruchsvoller" if est.band > eff else "wirkt einfacher"
        drivers = top_drivers(est)
        drv = f" (maßgeblich: {', '.join(drivers)})" if drivers else ""
        warnings.append(
            f"{b.id}: Schwierigkeit — berechnete Stufe {est.band} weicht von der "
            f"hinterlegten Stufe {eff} ({quelle}) ab; Aufgabe {richtung}. Einstufung als "
            f"Prüf-Hinweis überdenken, keine Korrektur{drv}."
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
