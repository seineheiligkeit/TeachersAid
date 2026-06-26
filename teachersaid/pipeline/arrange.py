"""Assemble / derive / verify for a Lernarrangement (schema v0.5) — DETERMINISTIC.

Reuses the worksheet pipeline entirely: each role's material is assembled/verified
as a normal worksheet, then the arrangement-level Nachweis is the **union of the
role Nachweise plus the competence_anchors** — the latter are how the oral / social
/ enactive competences (reached by the interaction, debrief, or shared product, not
by any printable sheet) enter coverage. depth_profile is the aggregate over all
role tasks. As with a worksheet, these DERIVED fields are never authored by hand.
"""

from __future__ import annotations

from collections import defaultdict

from ..schema.arrangement import GROUPINGS, SERVED_BY, Lernarrangement
from ..schema.derived import CompetenceCoverage, DepthProfile, Nachweis
from ..schema.enums import CoverageRelation, Role
from ..schema.worksheet import LehrplanResolution
from .assemble import assemble
from .verify import VerifyReport, verify


def _aggregate_depth(arr: Lernarrangement) -> DepthProfile:
    by_level: dict[str, int] = defaultdict(int)
    by_dimension: dict[str, int] = defaultdict(int)
    minutes_total = minutes_ri = 0
    for role in arr.roles:
        dp = role.material.depth_profile
        if dp is None:
            continue
        for k, v in dp.by_level.items():
            by_level[k] += v
        for k, v in dp.by_dimension.items():
            by_dimension[k] += v
        minutes_total += dp.minutes_total
        minutes_ri += dp.minutes_resource_independent
    return DepthProfile(
        by_level=dict(by_level), by_dimension=dict(by_dimension),
        minutes_total=minutes_total, minutes_resource_independent=minutes_ri,
    )


def derive_arrangement_nachweis(
    arr: Lernarrangement, resolution: LehrplanResolution
) -> Nachweis:
    """⋃ of the roles' exercised competences + the arrangement-level anchors.
    A competence covered ONLY by an anchor is the v0.5 payoff: the worksheet
    couldn't reach it, the arrangement does."""
    exercised: dict[str, list[str]] = defaultdict(list)
    for role in arr.roles:
        for b in role.material.iter_blocks():
            if b.role != Role.TASK:
                continue
            for s in b.serves:
                if s.relation == CoverageRelation.EXERCISES:
                    exercised[s.competence_id].append(f"{role.id}:{b.id}")

    anchored: dict[str, list[str]] = defaultdict(list)
    for a in arr.competence_anchors:
        anchored[a.competence_id].append(a.served_by)

    universe = {c.id: c for c in resolution.competences}
    for cid in list(exercised) + list(anchored):
        universe.setdefault(cid, None)

    coverage: list[CompetenceCoverage] = []
    gaps: list[str] = []
    uet: set[int] = set()
    konzepte: set[str] = set()
    anchor_only = 0
    for cid, comp in universe.items():
        ex = exercised.get(cid, [])
        an = anchored.get(cid, [])
        covered = bool(ex) or bool(an)
        coverage.append(CompetenceCoverage(
            competence_id=cid,
            exercised_by=ex + [f"anchor:{s}" for s in an],
            covered=covered,
        ))
        if covered and not ex and an:
            anchor_only += 1
        if comp is not None:
            konzepte.add(comp.kompetenzbereich)
            if covered:
                uet.update(comp.uebergreifende_themen)
        if not covered:
            gaps.append(f"{cid} — {comp.text if comp is not None else cid}")

    n_cov = sum(1 for c in coverage if c.covered)
    statement = (
        f"Dieses Lernarrangement adressiert {n_cov} von {len(coverage)} verbatim "
        f"Kompetenzen des Lehrplans (davon {anchor_only} über Interaktion, Debrief "
        f"oder gemeinsames Produkt verankert — nicht über ein einzelnes Arbeitsblatt), "
        f"gebunden an {resolution.fassung.bgbl} (DokNr {resolution.fassung.doknr})."
    )
    return Nachweis(
        fassung=resolution.fassung.model_dump(),
        statement=statement,
        competence_coverage=coverage,
        gaps=gaps,
        zentrale_konzepte=sorted(konzepte),
        uebergreifende_themen=sorted(uet),
    )


def assemble_arrangement(
    arr: Lernarrangement, resolution: LehrplanResolution
) -> Lernarrangement:
    """Assemble each role's material (its own Nachweis/DepthProfile), then fill the
    arrangement-level DERIVED fields."""
    for role in arr.roles:
        assemble(role.material, resolution)
    arr.depth_profile = _aggregate_depth(arr)
    arr.nachweis = derive_arrangement_nachweis(arr, resolution)
    return arr


def verify_arrangement(
    arr: Lernarrangement, resolution: LehrplanResolution
) -> VerifyReport:
    """Every role's material verifies as a worksheet (kinds/dims/coverage/media);
    plus arrangement-level rules: roles exist, phases are well-formed, and every
    anchor references a resolved competence + a valid served_by."""
    problems: list[str] = []
    warnings: list[str] = []

    if not arr.roles:
        problems.append("arrangement has no roles")

    for role in arr.roles:
        rep = verify(role.material, resolution)
        problems += [f"role '{role.id}': {p}" for p in rep.problems]
        warnings += [f"role '{role.id}': {w}" for w in rep.warnings]

    for ph in arr.phases:
        if ph.grouping not in GROUPINGS:
            problems.append(f"phase '{ph.id}': invalid grouping '{ph.grouping}'")
        if ph.minutes <= 0:
            warnings.append(f"phase '{ph.id}': non-positive minutes")

    valid_ids = {c.id for c in resolution.competences}
    role_ids = {r.id for r in arr.roles}
    if not arr.competence_anchors:
        warnings.append("no competence_anchors — an arrangement with no oral/social "
                        "anchor is just stapled worksheets")
    for a in arr.competence_anchors:
        if valid_ids and a.competence_id not in valid_ids:
            problems.append(f"anchor: unknown competence '{a.competence_id}'")
        ok = a.served_by in SERVED_BY or (
            a.served_by.startswith("role:") and a.served_by[5:] in role_ids)
        if not ok:
            problems.append(f"anchor '{a.competence_id}': invalid served_by '{a.served_by}'")

    return VerifyReport(ok=not problems, problems=problems, warnings=warnings)
