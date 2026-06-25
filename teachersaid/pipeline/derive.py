"""Derived coverage + depth (schema §5) — DETERMINISTIC.

These functions are the data-level guarantee behind "shallow" and "coverage gap"
being measurements, not judgement calls. They are the ONLY producers of Nachweis
and DepthProfile; the LLM never authors them.
"""

from __future__ import annotations

from collections import defaultdict

from ..schema.competence import SubjectCompetenceModel, printable_coverage
from ..schema.derived import CompetenceCoverage, DepthProfile, Nachweis
from ..schema.enums import CoverageRelation, Role
from ..schema.worksheet import LehrplanResolution, WorksheetContent

__all__ = ["compute_depth", "derive_nachweis", "printable_coverage"]


def _task_blocks(content: WorksheetContent):
    for b in content.iter_blocks():
        if b.role == Role.TASK:
            yield b


def compute_depth(content: WorksheetContent) -> DepthProfile:
    """Cognitive profile over all TaskBlocks. by_dimension counts the PRIMARY
    dimension (dimensions[0]) per task — the 'primary first' convention (§8)."""
    by_level: dict[str, int] = defaultdict(int)
    by_dimension: dict[str, int] = defaultdict(int)
    minutes_total = 0
    minutes_ri = 0
    for b in _task_blocks(content):
        by_level[b.cognitive_level] += 1
        if b.dimensions:
            by_dimension[b.dimensions[0]] += 1
        minutes_total += b.est_minutes
        if not (b.flags and b.flags.equipment_dependent):
            minutes_ri += b.est_minutes
    return DepthProfile(
        by_level=dict(by_level),
        by_dimension=dict(by_dimension),
        minutes_total=minutes_total,
        minutes_resource_independent=minutes_ri,
    )


def derive_nachweis(
    content: WorksheetContent, resolution: LehrplanResolution
) -> Nachweis:
    """Aggregate every TaskBlock.serves across all blocks. A competence in the
    resolution with zero exercising blocks surfaces automatically as a gap —
    this is how STR.01 'Quellen bewerten' shows up uncovered (schema §5/§8)."""
    exercised: dict[str, list[str]] = defaultdict(list)
    prereq: dict[str, list[str]] = defaultdict(list)
    for b in _task_blocks(content):
        for s in b.serves:
            if s.relation == CoverageRelation.EXERCISES:
                exercised[s.competence_id].append(b.id)
            else:
                prereq[s.competence_id].append(b.id)

    universe = {c.id: c for c in resolution.competences}
    # include any served competence not in the resolution universe (defensive)
    for cid in list(exercised) + list(prereq):
        universe.setdefault(cid, None)

    coverage: list[CompetenceCoverage] = []
    gaps: list[str] = []
    uet: set[int] = set()
    konzepte: set[str] = set()
    for cid, comp in universe.items():
        covered = bool(exercised.get(cid))
        coverage.append(
            CompetenceCoverage(
                competence_id=cid,
                exercised_by=exercised.get(cid, []),
                prerequisite_by=prereq.get(cid, []),
                covered=covered,
            )
        )
        if comp is not None:
            konzepte.add(comp.kompetenzbereich)
            if covered:
                uet.update(comp.uebergreifende_themen)
        if not covered:
            label = comp.text if comp is not None else cid
            gaps.append(f"{cid} — {label}")

    n_cov = sum(1 for c in coverage if c.covered)
    statement = (
        f"Diese Materialien adressieren {n_cov} von {len(coverage)} verbatim "
        f"Kompetenzen des Lehrplans, gebunden an {resolution.fassung.bgbl} "
        f"(DokNr {resolution.fassung.doknr})."
    )
    return Nachweis(
        fassung=resolution.fassung.model_dump(),
        statement=statement,
        competence_coverage=coverage,
        gaps=gaps,
        zentrale_konzepte=sorted(konzepte),
        uebergreifende_themen=sorted(uet),
    )
